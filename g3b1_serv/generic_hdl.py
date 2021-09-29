import functools
import importlib
from _ast import FunctionDef

from sqlalchemy import MetaData, Table, select
from sqlalchemy.engine import Engine, Result, Row
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from g3b1_cfg.tg_cfg import G3Context
from g3b1_cfg.tg_cfg import ins_g3_m, sel_g3_m
from g3b1_data import settings
from g3b1_data.elements import ELE_TY_user_id, ELE_TY_su__user_id, ELE_TY_out__chat_id
from g3b1_data.entities import EntTy, EntId
from g3b1_data.model import G3Command, G3Module, g3m_str_by_file_str, MenuIt, G3Arg
from g3b1_serv import utilities
from g3b1_serv.tg_reply import bold
from g3b1_serv.utilities import upd_extract_chat_user_id, sql_rs_2_tbl
from g3b1_ui.model import TgUIC
from subscribe.data.db import eng_SUB, md_SUB
from subscribe.serv import services as sub_services


def init_g3_ctx(upd: Update, ctx: CallbackContext):
    G3Context.upd = upd
    G3Context.ctx = ctx
    G3Context.g3_cmd = None
    G3Context.g3_m_str = None
    setng = settings.cu_setng(ELE_TY_su__user_id)
    setng['user_id'] = G3Context.user_id()
    G3Context.su__user_id = settings.read_setting(eng_SUB, md_SUB, setng).result
    setng['ele_ty'] = ELE_TY_out__chat_id
    G3Context.out__chat_id = settings.read_setting(eng_SUB, md_SUB, setng).result
    TgUIC.uic = TgUIC(upd)
    g3_m_str = ctx.bot.username.split('_')[1]
    if g3_m_str == 'translate':
        g3_m_str = 'trans'

    G3Context.g3_m_str = g3_m_str


def tg_handler():
    def decorator_handler(cmd_func):
        @functools.wraps(cmd_func)
        def wrapper_handler(*arg, **kwargs):
            """arg should have 2 entries only: upd and ctx
            upd contains user_id and chat_id *required by many handlers, passed depending on funcdef*
            kwargs contains additional hdl specific parameters found.
            Their values are found in ctx.args as well if called from TG API
              """
            upd: Update = arg[0]
            ctx_args = []
            # ctx: CallbackContext = None
            # if len(arg) > 1:
            ctx: CallbackContext = arg[1]
            if ctx and ctx.args:
                ctx_args = ctx.args
            init_g3_ctx(upd, ctx)

            g3_cmd: G3Command = utilities.g3_cmd_by_func(cmd_func)
            G3Context.g3_cmd = g3_cmd
            G3Context.g3_m_str = g3_cmd.g3_m.name

            # noinspection PyTypeChecker
            ent_ty: EntTy = None
            if g3_cmd.has_arg_ent_ty():
                # args extraction for generic commands
                ent_ty = kwargs['ent_ty']
                kwargs.pop('ent_ty')

            # Have kwargs been passed by the caller and are missing in ctx.args?
            # Then we rebuild ctx.args from kwargs
            # Simple g3b1_test, i.e. no analysis of possible mismatches
            # A handler method can therefore be called by populating kwargs or ctx.args (in the right order)
            if len(kwargs) > 0 and len(kwargs) > len(ctx_args):
                ctx_args.clear()
                for kw in kwargs:
                    if len(kwargs) == 1:
                        """This makes no sense, maybe we pass title = 'hello world' and 
                        have then len(ctx.args) == 2 Why should we want this?
                        And the other way around is missing, isn't it?
                        Aha! Check the join part below. Parsing single title alike args with possible spaces 
                        """
                        split_li = str(kwargs[kw]).split(' ')
                        ctx_args.extend(split_li)
                    else:
                        ctx_args.append(kwargs[kw])
            # At this point kwargs could be cleared to ensure
            # same state, no matter where we come from (testcase, TG, click cmd)

            idx_last_ctx_arg = len(ctx_args) - 1
            cmd_arg_li = [i for i in g3_cmd.extra_args() if
                          (i.f_current == False)]  # skipping upd, chat_id, user_id and more
            for idx, item in enumerate(cmd_arg_li):
                if idx <= idx_last_ctx_arg:
                    # if len(cmd_arg_li) == 1 and len(ctx_args):
                    #     # A title like argument with spaces will be split into several args by PTB
                    #     kwargs.update({item.arg: ' '.join(ctx_args)})
                    # else:
                    if idx == len(cmd_arg_li) - 1:
                        arg_val = ' '.join(ctx_args[idx:])
                    else:
                        arg_val = ctx_args[idx]
                    if item.arg == 'uname' and arg_val and len(arg_val) < 6:
                        arg_val = 'g3b1_' + arg_val
                    if item.arg == 'req__user_id':
                        req__user_id = sub_services.id_by_uname(arg_val)
                        if not req__user_id:
                            TgUIC.uic.err_p_404(arg_val, ELE_TY_user_id)
                            return
                        arg_val = req__user_id
                    kwargs.update({item.arg: arg_val})
                else:
                    kwargs.update({item.arg: None})
            ent_ty_arg_li = g3_cmd.ent_ty_args()
            if ent_ty_arg_li:
                modu_db = importlib.import_module(f'{G3Context.g3_m_str}.data.db')
                # noinspection PyArgumentList
                sel_ent_ty = getattr(modu_db, 'sel_ent_ty', 'NULL')
                for g3_arg in ent_ty_arg_li:
                    if g3_arg.f_current:
                        ent_r_id = settings.ent_by_setng(upd_extract_chat_user_id(), g3_arg.ele_ty,
                                                         ent_ty=g3_arg.ent_ty).result
                    elif g3_arg.f_required:
                        ent_r_id = kwargs[g3_arg.arg]
                        if ent_r_id and str(ent_r_id).isnumeric():
                            ent_r_id = int(ent_r_id)
                    else:
                        ent_r_id = 0
                    if isinstance(ent_r_id, int) and ent_r_id:
                        ent_r = sel_ent_ty(EntId(g3_arg.ent_ty, ent_r_id)).result
                        kwargs.update({g3_arg.arg: ent_r})
                    else:
                        kwargs.update({g3_arg.arg: None})

            new_arg_li = []
            chat_id = upd.effective_chat.id
            user_id = upd.effective_user.id
            reply_to_msg = upd.effective_message.reply_to_message
            if g3_cmd.has_arg_upd():
                new_arg_li.append(upd)
            if g3_cmd.has_arg_ctx():
                new_arg_li.append(ctx)
            if g3_cmd.has_arg_reply_to_msg() or g3_cmd.has_arg_src_msg():
                if g3_cmd.has_arg_reply_to_msg():
                    new_arg_li.append(reply_to_msg)
                if g3_cmd.has_arg_src_msg():
                    src_msg = None
                    if reply_to_msg:
                        src_msg = reply_to_msg
                    else:
                        if utilities.is_msg_w_cmd(upd.effective_message.text):
                            # src_msg is the message assumed to be the input for the command
                            # if no msg has been replied to
                            # it can not be safely guessed to be the latest chat-message
                            src_msg = utilities.read_latest_message(chat_id, user_id)
                    new_arg_li.append(src_msg)
            if g3_cmd.has_arg_reply_to_user_id():
                if reply_to_msg:
                    from_user_id = reply_to_msg.from_user.id
                else:
                    from_user_id = None
                new_arg_li.append(from_user_id)
            if g3_cmd.has_arg_chat():
                new_arg_li.append(chat_id)
            if g3_cmd.has_arg_user():
                new_arg_li.append(user_id)
            if g3_cmd.has_arg_ent_ty():
                new_arg_li.append(ent_ty)

            output = cmd_func(*new_arg_li, **kwargs)
            if (g3_cmd.is_ins_ent() or g3_cmd.is_pick_ent()) and output:
                settings.ent_to_setng(
                    upd_extract_chat_user_id(), output)
            G3Context.reset()
            return output

        return wrapper_handler

    return decorator_handler


@tg_handler()
def cmd_ent_ty_33_li(upd: Update, ent_ty: EntTy):
    chat_id, user_id = upd_extract_chat_user_id()
    md: MetaData = getattr(
        importlib.import_module(f'{ent_ty.g3_m_str}.data'), f'md_{ent_ty.g3_m_str.upper()}'
    )
    eng: Engine = getattr(
        importlib.import_module(f'{ent_ty.g3_m_str}.data'), f'eng_{ent_ty.g3_m_str.upper()}'
    )
    # ent_type = getattr(
    #     importlib.import_module(f'{ent_ty.g3_m_str}.data.model'), f'{ent_ty.type}_'
    # )
    tbl: Table = md.tables[ent_ty.tbl_name]
    with eng.begin() as con:
        c = tbl.columns
        if 'chat_id' in c:
            stmnt = (select(tbl).where(c.chat_id == chat_id))
        else:
            stmnt = (select(tbl))
        rs: Result = con.execute(stmnt)
        row_li: list[Row] = rs.fetchall()
    # noinspection PyTypeChecker
    col_li = [col for col in tbl.columns if col.key != 'chat_id']
    tg_tbl = sql_rs_2_tbl(row_li, col_li, tbl.name)
    if row_li:
        TgUIC.uic.send_tg_tbl(tg_tbl)
    else:
        TgUIC.uic.no_data()
    # ele_mebrs_tup_li = utilities.extract_ele_members(ent_type)
    #
    # ent_r_li: list = []
    # with eng.begin() as con:
    #     tbl: Table = md.tables[ent_ty.tbl_name]
    #     sel: Select = tbl.select()
    #     r: Result = con.execute(sel)
    #     row_li: list[Row] = r.fetchall()
    #     for row in row_li:
    #         ent_r = ent_type.from_row(row)
    #         ent_r_li.append(ent_r)
    #
    # col_li: list[TgColumn] = []
    # for tup in ele_mebrs_tup_li:
    #     id_ = tup[1].ele.id_
    #     position = ent_type.col_order_li().index(id_) + 1
    #     col_li.append(
    #         TgColumn(id_, position, tup[1].ele.col_name, tup[1].ele.ui_len)
    #     )
    # tbl_def = TableDef(col_li)
    #
    # val_dct_li: list[dict] = []
    # for ent_r in ent_r_li:
    #     ele_mebrs_tup_li = utilities.extract_ele_members(ent_r)
    #     val_dct: dict = {}
    #     for i in [i for i in ele_mebrs_tup_li if isinstance(i[1], EleVal)]:
    #         if i[1].val_mp:
    #             val_dct[i[0]] = i[1].val_mp
    #         else:
    #             val_dct[i[0]] = i[1].val
    #     val_dct_li.append(val_dct)
    #
    # tg_reply.send_table(upd, tbl_def, val_dct_li, '')


def init_g3_m_dct():
    g3_m = sel_g3_m(g3m_str_by_file_str(__file__))
    if not g3_m:
        print('Initialize G3_M_DCT')
        g3_m: G3Module = G3Module(__file__, {})

        func_def: FunctionDef = utilities.read_function(__file__,
                                                        cmd_ent_ty_33_li.__name__)
        # noinspection PyUnresolvedReferences
        g3_cmd: G3Command = G3Command(g3_m, cmd_ent_ty_33_li,
                                      [G3Arg(arg.arg, arg.annotation.id) for arg in func_def.args.args])
        g3_m.cmd_dct['ent_ty_33_li'] = g3_cmd
        ins_g3_m(g3_m)


def send_ent_ty_keyboard(ent_ty: EntTy):
    keyboard = []
    for but_row in ent_ty.but_cmd_li:
        key_li = [but[0] for but in but_row]
        keyboard.append(key_li)

    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard=True,
                                       resize_keyboard=True)
    TgUIC.uic.send(ent_ty.keyboard_descr, reply_markup=reply_markup)


def send_menu_keyboard(root_str: str, mi_li: list[MenuIt]):
    keyboard = []
    kb_row = []
    for mi in mi_li:
        if mi.lbl == '\n':
            keyboard.append(kb_row)
            kb_row = []
            continue
        menu_id = ''
        if mi.menu:
            menu_id = mi.menu.id + ':'
        elif mi.g3_cmd:
            menu_id = mi.g3_cmd.g3_m.name + ':'
        kb_row.append(InlineKeyboardButton(mi.lbl_w_icon(), callback_data=f'{menu_id}{mi.id}'))
    keyboard.append(kb_row)

    # ReplyKeyboardMarkup
    reply_markup = InlineKeyboardMarkup(keyboard)

    send_str = f'Choose a menu item for {bold(root_str)}'
    TgUIC.uic.send(send_str, reply_markup)


init_g3_m_dct()
