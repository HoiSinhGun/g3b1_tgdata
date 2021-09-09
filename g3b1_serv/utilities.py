import ast
import inspect
import os
from ast import FunctionDef
from datetime import datetime
from sqlite3 import Row
from typing import Any

from telegram import Update, Message

from g3b1_data import tg_db
from g3b1_serv import tg_reply
# import subscribe_main
from generic_mdl import *
from model import G3Module, g3_m_dct, G3Command, script_by_file_str

logger = cfg_logger(logging.getLogger(__name__), logging.WARN)


def extract_ele_members(ent_type: type) -> list[tuple[str, Any]]:
    mebrs_tup_li: list[tuple] = inspect.getmembers(ent_type)
    ele_mebrs_tup_li = [i for i in mebrs_tup_li if i[0][:2] != '__' and not inspect.isfunction(i[1])]
    return ele_mebrs_tup_li


def read_function(py_file: str, func_name: str) -> FunctionDef:
    logger.debug(str(f'Read function {func_name}'))
    with open(py_file) as file:
        node = ast.parse(file.read())
    n: FunctionDef
    func_li = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == func_name]
    return func_li[0]


def read_functions(py_file: str):
    filename = py_file
    with open(filename) as file:
        node = ast.parse(file.read())
    n: FunctionDef

    func_li = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name.startswith('cmd_')]

    # for function in func_li:
    #    print(function.name)
    return func_li


def g3_m_dct_init(g3_m_file: str) -> G3Module:
    g3_m = G3Module(g3_m_file)
    cmd_dct = {}
    hdl: ast.FunctionDef
    hdl_li = read_functions(g3_m_file)
    for hdl in hdl_li:
        script = script_by_file_str(g3_m.file_main)
        cpl = compile(f"import {g3_m.name}\nfrom {g3_m.name} import {script}\n", "<string>", "exec")
        exec(cpl)
        g3_cmd = G3Command(g3_m, eval(f'{g3_m.name}.{script}.{hdl.name}'), hdl.args.args)
        cmd_dct.update({g3_cmd.name: g3_cmd})
        logger.debug(g3_cmd)
    g3_m.cmd_dct = cmd_dct
    g3_m_dct.update({g3_m.name: g3_m})
    return g3_m


def lod_to_dic(lod: list) -> dict:
    count: int = 1
    data_as_dic: dict = {}
    for i in lod:
        data_as_dic.update({count: i})
        count += 1
    return data_as_dic


def dc_dic_to_table(dc_dic: dict, tbl_def: TableDef) -> TgTable:
    row_li: list[dict[str, str]] = []
    for k, v in dc_dic.items():
        val_dic: dict
        if type(v) is dict:
            val_dic = v
        else:
            val_dic = v.as_dict_ext()
        row_li.append(val_dic)
    return row_li_to_table(row_li, tbl_def)


def row_li_to_table(row_li: list[dict], tbl_def: TableDef) -> TgTable:
    tbl: TgTable = TgTable(tbl_def, col_li=tbl_def.col_li)
    # count_col: int = 0
    for count, val_dic in enumerate(row_li):
        row_nr = count + 1
        row: TgRow = TgRow(tbl, str(count), row_nr, [], val_dic)
        tbl.row_li.append(row)
        if not TgColumn.contains_col_with(tbl.col_li, COL_POS.key):
            tbl.col_li.append(TgColumn(COL_POS.key, COL_POS.pos, COL_POS.col_name, COL_POS.width))
        for k_, v_ in val_dic.items():
            if not TgColumn.is_allow_col_with(tbl.tbl_def.col_li, k_):
                continue
            if TgColumn.contains_col_with(tbl.col_li, k_):
                continue
            tbl_def_col = TgColumn.col_by(tbl_def.col_li, k_)
            col: TgColumn = TgColumn(tbl_def_col.key, -1, tbl_def_col.col_name, width=tbl_def_col.width)
            tbl.col_li.append(col)
    return tbl


def print_header_line(text: str):
    print("".ljust(80, "="))
    print(f'=== {text.upper()} '[:76].ljust(76) + ' ===')
    print("".ljust(80, "="))


def g3_cmd_by_func(cmd_func) -> G3Command:
    func_module_str = str(cmd_func.__module__).split(".")[0]
    if func_module_str.startswith('generic'):
        func_module_str = 'generic'
    g3_m_str = func_module_str
    g3_m: G3Module = g3_m_dct[g3_m_str]
    prefix: str = f'cmd_'  # {g3_m_str}_'
    len_prefix: int = len(prefix)
    f_name = str(cmd_func.__name__)
    cmd_name = f_name[len_prefix:len(f_name)]
    cmd_name = cmd_name.replace(f'{g3_m_str}_', "")
    g3_cmd: G3Command = g3_m.cmd_dct[cmd_name]
    return g3_cmd


def module_by_inspect() -> str:
    module = c_info_by_inspect()[1].split("_")[0]
    logger.debug(f"module requested: {module}")
    return module


def c_info_by_inspect() -> (str, str):
    # first get the full filename (including path and file extension)
    # print(inspect.stack())
    caller_frame = inspect.stack()[2]
    caller_filename_full = caller_frame.filename

    # now get rid of the directory (via basename)
    # then split filename and extension (via splitext)
    caller_filename_only = os.path.splitext(os.path.basename(caller_filename_full))[0]

    # return both filename versions as tuple
    return caller_filename_full, caller_filename_only


def table_print(tbl: TgTable, idx_from=0, idx_to=-1) -> str:
    if idx_to == -1 or idx_to >= len(tbl.row_li):
        idx_to = len(tbl.row_li)

    if idx_to == -1 or idx_from >= idx_to:
        return ''

    row: TgRow
    col: TgColumn
    col_key: str
    cel_val: str
    row_str: str
    tbl_str: str = ""
    for row in tbl.row_li[idx_from:idx_to]:
        row_str = ""
        for col in tbl.tbl_def.col_li:
            if col.key == COL_POS.key:
                pos = str(tbl.row_li.index(row) + 1)
                cel_val = pos
                # cel_val = f'<a href="/dl_{pos}">{pos}</a>'
                # url = create_deep_linked_url('@g3b1_translate_bot', pos)
                # cel_val = f'{pos}: <a href={url}>{pos}</a>'
            elif col.key not in row.val_dic.keys():
                row_str = row_str + str('').ljust(col.width) + " | "
                continue
            else:
                cel_val = str(row.val_dic[col.key])
            cel_val = str(cel_val[:col.width]).ljust(col.width)
            row_str = row_str + cel_val + " | "
        tbl_str = tbl_str + f'{row_str}\n'
    row_str = ''
    row_hr = ''
    for col in tbl.tbl_def.col_li:
        row_hr = row_hr + str('').ljust(col.width, '_') + '___'
        row_str = row_str + str(col.col_name[:col.width]).ljust(col.width) + " | "
    tbl_str = f'{row_hr}\n{row_str}\n{row_hr}\n{tbl_str}{row_hr}'

    # if logger.isEnabledFor(logging.DEBUG):
    #    logger.debug(f'\n{tbl_str}')
    return tbl_str


def build_commands_str(commands: dict[str, G3Command], cmd_scope=''):
    commands_str = ''
    for key, g3_cmd in commands.items():
        args_str = '['
        for item in g3_cmd.extra_args():
            args_str += item.arg + ', '
        args_str = args_str[:len(args_str) - 2] + ']'
        if not cmd_scope or g3_cmd.name[:len(cmd_scope)] == cmd_scope:
            commands_str += f'/{g3_cmd.name} {args_str}: {g3_cmd.description}\n'
    return commands_str


def build_debug_str(update: Update) -> str:
    return f'Your chat id is <code>{update.effective_chat.id}</code>.\n' \
           f'Your user id is <code>{update.effective_user.id}</code>.\n'


def now_for_sql() -> str:
    # datetime object containing current date and time
    now = datetime.now()
    # The sqlite datetime() function returns "YYYY-MM-DD HH:MM:SS
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
    return dt_string


def tst_for_sql() -> str:
    # datetime object containing current date and time
    now = datetime.now()
    # The sqlite datetime() function returns "YYYY-MM-DD HH:MM:SS.mmmmmmm
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S.%f")
    return dt_string


def upd_extract_chat_user_id(upd: Update) -> (int, int):
    return upd.effective_chat.id, upd.effective_user.id


def read_latest_cmd(upd: Update, g3_m: G3Module) -> Message:
    return read_latest_message(*upd_extract_chat_user_id(upd), is_cmd_explicit=True, g3_m=g3_m)


def read_latest_message(chat_id, user_id, is_cmd_explicit=False, g3_m: G3Module = None) -> Message:
    g3m_str = g3_m.name if g3_m else ''
    row: Row = tg_db.read_latest_message(chat_id, user_id, is_cmd_explicit, g3m_str).result
    if not row:
        # noinspection PyTypeChecker
        return None
    dt_object = datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S')
    message = Message(row['ext_id'], dt_object, row['tg_chat_id'],
                      row['tg_user_id'], text=row['text'])
    return message


def hdl_retco(upd: Update, logto: logging.Logger, retco):
    if not retco or retco[0] != 0:
        logto.error(f'retco: {retco}')
        tg_reply.cmd_err(upd)
        return

    tg_reply.cmd_success(upd)
    return


def is_msg_w_cmd(text: str = None) -> bool:
    return text.startswith('.') or text.startswith('/')
