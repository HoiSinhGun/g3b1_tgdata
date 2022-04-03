import ast
import importlib
import logging
from _ast import FunctionDef
from functools import cache
from typing import Any

from sqlalchemy import MetaData, create_engine, Table, delete, select, insert, asc
from sqlalchemy.engine import Connection, CursorResult, Row, Engine
from telegram import Update, File
from telegram.ext import CallbackContext

from constants import env_g3b1_dir, env_g3b1_code, g3b1_dir_files
from elements import EleTy
from g3b1_data.entities import EntTy
from g3b1_data.model import G3Command, G3Module, G3Arg, script_by_file_str, G3Func
from g3b1_log.log import cfg_logger
from generic_mdl import get_ele_ty_li, get_ent_ty_li
from py_meta import read_functions, read_function, build_module_str

logger = cfg_logger(logging.getLogger(__name__), logging.WARN)

db_file_cfg = rf'{env_g3b1_dir}\g3b1_cfg.db'
md_cfg = MetaData()
eng_cfg = create_engine(f"sqlite:///{db_file_cfg}")


class G3Ctx:
    upd: "Update" = None
    ctx: CallbackContext = None
    su__user_id: int = None
    out__chat_id: int = None
    g3_m_str: str = None
    g3_cmd: "G3Command" = None
    eng: Engine = None
    md: MetaData = None

    @classmethod
    def as_dict(cls):
        return {'upd': cls.upd, 'ctx': cls.ctx, 'su__user_id': cls.su__user_id,
                'out__chat_id': cls.out__chat_id, 'g3_m_str': cls.g3_m_str,
                'g3_cmd': cls.g3_cmd, 'eng': cls.eng, 'md': cls.md, 'ctx_args': cls.ctx.args}

    @classmethod
    def from_dict(cls, v: dict):
        cls.upd = v['upd']
        cls.ctx = v['ctx']
        cls.ctx.args = v['ctx_args']
        cls.su__user_id = v['su__user_id']
        cls.out__chat_id = v['out__chat_id']
        cls.g3_m_str = v['g3_m_str']
        cls.g3_cmd = v['g3_cmd']
        cls.eng = v['eng']
        cls.md = v['md']

    # noinspection PyTypeChecker
    @classmethod
    def reset(cls):
        cls.upd = None
        cls.ctx = None
        cls.su__user_id = None
        cls.out__chat_id = None
        cls.g3_cmd = None
        cls.g3_m_str = None
        # Set when bot starts up
        # cls.eng = None
        # cls.md = None

    @classmethod
    def get_tg_files_dir(cls) -> str:
        return g3b1_dir_files

    @classmethod
    def get_tg_voice_file(cls) -> File:
        if cls.upd and cls.upd.effective_message.voice:
            return cls.upd.effective_message.voice.get_file()

    @classmethod
    def get_tg_aud_or_voi_file(cls) -> File:
        if cls.upd and cls.upd.effective_message.voice:
            return cls.upd.effective_message.voice.get_file()
        elif cls.upd and cls.upd.effective_message.audio:
            return cls.upd.effective_message.audio.get_file()

    @classmethod
    def chat_id(cls) -> int:
        if cls.upd:
            return cls.upd.effective_chat.id

    @classmethod
    def out_chat_id(cls) -> int:
        if cls.out__chat_id:
            return cls.out__chat_id
        return cls.chat_id()

    @classmethod
    def user_id(cls) -> int:
        if cls.upd:
            return cls.upd.effective_user.id

    @classmethod
    def for_user_id(cls) -> int:
        if cls.su__user_id:
            return cls.su__user_id
        return cls.user_id()

    @classmethod
    def cu_tup(cls) -> (int, int):
        return cls.chat_id(), cls.for_user_id()


def init_g3_m(g3_m_file: str) -> G3Module:
    g3_m = G3Module(g3_m_file)
    cmd_dct = {}
    ent_ty_li: list[EntTy] = []
    if g3_m.name != 'generic':
        module_mdl = importlib.import_module(f'{g3_m.name}.data.model')
        ent_ty_li = getattr(module_mdl, f'ENT_TY_{g3_m.name}_li')

    hdl: ast.FunctionDef
    hdl_li = read_functions(g3_m_file, 'cmd_')
    for hdl in hdl_li:
        script = script_by_file_str(g3_m.file_main)
        cpl = compile(f"import {g3_m.name}\nfrom {g3_m.name} import {script}\n", "<string>", "exec")
        exec(cpl)
        # noinspection PyUnresolvedReferences
        g3_cmd = G3Command(g3_m, eval(f'{g3_m.name}.{script}.{hdl.name}'),
                           [G3Arg(arg.arg, G3Arg.get_annotation(arg), ent_ty_li, get_ele_ty_li(g3_m.name)) for arg in
                            hdl.args.args])
        cmd_dct.update({g3_cmd.name: g3_cmd})
        logger.debug(g3_cmd)
    g3_m.cmd_dct = cmd_dct
    ins_g3_m(g3_m)
    return g3_m


def del_g3_m_by_file(file: str):
    g3_m = G3Module(file)
    tbl_g3_m: Table = md_cfg.tables['g3_m']
    eng_cfg.execute(delete(tbl_g3_m).where(tbl_g3_m.c['name'] == g3_m.name))


def ins_g3_m(g3_m: G3Module):
    with eng_cfg.begin() as con:
        tbl_g3_m: Table = md_cfg.tables['g3_m']
        tbl_g3_cmd: Table = md_cfg.tables['g3_cmd']
        tbl_g3_cmd_arg: Table = md_cfg.tables['g3_cmd_arg']

        # noinspection PyPropertyAccess
        sel_stmnt = select(tbl_g3_m).where(tbl_g3_m.c['name'] == g3_m.name)
        rs: CursorResult = con.execute(sel_stmnt)
        if rs.first():
            return

        stmnt = insert(tbl_g3_m).values(dict(name=g3_m.name, file_main=g3_m.file_main))
        con.execute(stmnt)
        rs: CursorResult = con.execute(sel_stmnt)
        g3_m_id = rs.first()['id']
        for g3_cmd in g3_m.cmd_dct.values():
            stmnt = insert(tbl_g3_cmd).values(dict(g3_m_id=g3_m_id, name=g3_cmd.name,
                                                   long_name=g3_cmd.long_name, handler=g3_cmd.handler.__name__,
                                                   icon=g3_cmd.icon)
                                              )
            con.execute(stmnt)
            # noinspection PyPropertyAccess
            sel_stmnt = select(tbl_g3_cmd).where(tbl_g3_cmd.c.g3_m_id == g3_m_id, tbl_g3_cmd.c.name == g3_cmd.name)
            rs = con.execute(sel_stmnt)
            g3_cmd_id = rs.first()['id']
            g3_arg: G3Arg
            for idx, g3_arg in enumerate(g3_cmd.g3_arg_li):
                stmnt = insert(tbl_g3_cmd_arg).values(dict(g3_cmd_id=g3_cmd_id, arg=g3_arg.arg,
                                                           annotation=g3_arg.annotation, num=idx
                                                           ))
                con.execute(stmnt)


@cache
def sel_ele_ty_cls(ele_ty: EleTy) -> Any:
    tbl: Table = md_cfg.tables['ele_ty']
    stmnt = select(tbl).where(tbl.c.ele_ty == ele_ty.id_)
    cr: CursorResult = eng_cfg.execute(stmnt)
    if not (row := cr.first()):
        return
    module = importlib.import_module(row['module'])
    cls = getattr(module, row['cls_name'])
    return cls


def g3_cmd_by(g3_cmd_str: str) -> G3Command:
    return sel_g3_m(G3Ctx.g3_m_str).cmd_dct[g3_cmd_str]


@cache
def sel_g3_m(g3_m_str: str) -> G3Module:
    ent_ty_li: list[EntTy] = []
    if g3_m_str == 'generic':
        module_hdl = importlib.import_module(f'g3b1_serv.generic_hdl')
    else:
        module_hdl = importlib.import_module(f'{g3_m_str}.{g3_m_str}__tg_hdl')
        module_mdl = importlib.import_module(f'{g3_m_str}.data.model')
        ent_ty_li = getattr(module_mdl, f'ENT_TY_{g3_m_str}_li')
    with eng_cfg.begin() as con:
        tbl_g3_m: Table = md_cfg.tables['g3_m']
        tbl_g3_cmd: Table = md_cfg.tables['g3_cmd']
        tbl_g3_cmd_arg: Table = md_cfg.tables['g3_cmd_arg']
        sel_stmnt = select(tbl_g3_m).where(tbl_g3_m.c['name'] == g3_m_str)
        rs: CursorResult = con.execute(sel_stmnt)
        row = rs.first()
        if not row:
            # noinspection PyTypeChecker
            return
        g3_m: G3Module = G3Module(row['file_main'], {}, id_=row['id'])
        j = tbl_g3_cmd.join(tbl_g3_cmd_arg, isouter=True)
        sel_stmnt = select(tbl_g3_cmd, tbl_g3_cmd_arg.c.arg, tbl_g3_cmd_arg.c.annotation). \
            select_from(j).where(tbl_g3_cmd.c.g3_m_id == g3_m.id_).order_by(asc(tbl_g3_cmd_arg.c.num))
        rs = con.execute(sel_stmnt)
        row_li: list[Row] = rs.fetchall()
        for row in row_li:
            cmd_name = row['name']
            if cmd_name not in g3_m.cmd_dct.keys():
                handler = getattr(module_hdl, row['handler'])
                g3_m.cmd_dct[cmd_name] = G3Command(g3_m, handler, [])
            if not row['arg']:
                continue
            g3_cmd: G3Command = g3_m.cmd_dct[cmd_name]
            g3_cmd.g3_arg_li.append(G3Arg(row['arg'], row['annotation'], ent_ty_li, get_ele_ty_li(g3_m_str)))
    return g3_m


def del_db_cfg():
    con: Connection
    with eng_cfg.begin() as con:
        tbl_g3_m: Table = md_cfg.tables['g3_m']
        stmnt = delete(tbl_g3_m)
        con.execute(stmnt)


def init_g3_m_dct():
    g3_m = sel_g3_m('generic')
    if not g3_m:
        # g3b1_tgdata\
        generic_hdl_file_str = rf'{env_g3b1_code}\g3b1_tgdata\g3b1_serv\generic_hdl.py'
        print('Initialize G3_M_DCT')
        g3_m: G3Module = G3Module(generic_hdl_file_str, {})

        func_def: FunctionDef = read_function(generic_hdl_file_str,
                                              'cmd_ent_ty_33_li')
        module_hdl = importlib.import_module(f'g3b1_serv.generic_hdl')
        cmd_ent_ty_33_li = getattr(module_hdl, 'cmd_ent_ty_33_li')
        # noinspection PyUnresolvedReferences
        g3_cmd: G3Command = G3Command(g3_m, cmd_ent_ty_33_li,
                                      [G3Arg(arg.arg, arg.annotation.id) for arg in func_def.args.args])
        g3_m.cmd_dct['ent_ty_33_li'] = g3_cmd
        ins_g3_m(g3_m)


def del_g3_m_of_scripts(script_li: list[str]):
    for script in script_li:
        del_g3_m_by_file(script)


def init_g3_m_for_scripts(script_li: list[str], g3_m_str_li: list[str]):
    return
    # noinspection PyUnreachableCode
    for script_long in script_li:
        module_str = build_module_str(script_long)
        # g3_m = sel_g3_m(module_str)
        func_li = read_functions(script_long)
        # script = script_by_file_str(script_long)
        module = importlib.import_module(module_str)

        ent_ty_li = get_ent_ty_li(g3_m_str_li)
        ele_ty_li = get_ele_ty_li(g3_m_str_li)
        for func in func_li:
            # the return type...do we need it?
            g3_func: G3Func = G3Func(g3_m, getattr(module, func.name), func.name,
                                     [G3Arg(arg.arg, G3Arg.get_annotation(arg), ent_ty_li, ele_ty_li) for arg
                                      in
                                      func.args.args])
            logger.debug(g3_func)
        # ins_g3_m(g3_m)


def init_cfg():
    init_db_cfg()
    init_g3_m_dct()


def init_db_cfg():
    con: Connection
    with eng_cfg.begin() as con:  #
        g3_m_create = 'CREATE TABLE IF NOT EXISTS "g3_m" ( ' \
                      '"id"	INTEGER NOT NULL,' \
                      '"name"	TEXT NOT NULL,' \
                      '"file_main" TEXT NOT NULL,' \
                      'UNIQUE("name"),' \
                      'PRIMARY KEY("id" AUTOINCREMENT)' \
                      ')'
        #
        g3_cmd_create = 'CREATE TABLE IF NOT EXISTS "g3_cmd" (' \
                        '"id"	INTEGER NOT NULL,' \
                        '"g3_m_id"	INTEGER NOT NULL,' \
                        '"name"	TEXT NOT NULL,' \
                        '"long_name"	TEXT NOT NULL,' \
                        '"handler"	TEXT NOT NULL,' \
                        'UNIQUE("g3_m_id", "name"),' \
                        'FOREIGN KEY ("g3_m_id") REFERENCES "g3_m"("id") ON DELETE CASCADE,' \
                        'PRIMARY KEY("id" AUTOINCREMENT))'
        g3_cmd_arg_create = 'CREATE TABLE IF NOT EXISTS  "g3_cmd_arg" (' \
                            '"id"	INTEGER NOT NULL,' \
                            '"g3_cmd_id"	INTEGER NOT NULL,' \
                            '"num"	INTEGER NOT NULL,' \
                            '"arg"	TEXT NOT NULL,' \
                            '"annotation"	TEXT,' \
                            'UNIQUE("g3_cmd_id", "arg"),' \
                            'UNIQUE("g3_cmd_id", "num"),' \
                            'FOREIGN KEY ("g3_cmd_id") REFERENCES "g3_cmd"("id") ON DELETE CASCADE,' \
                            'PRIMARY KEY("id" AUTOINCREMENT))'
        #
        con.execute(g3_m_create)
        con.execute(g3_cmd_create)
        con.execute(g3_cmd_arg_create)
    md_cfg.reflect(bind=eng_cfg)
