import inspect
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Tuple, Optional

from sqlalchemy.engine import Row
from telegram import Update, Message

from g3b1_cfg.tg_cfg import sel_g3_m, G3Ctx
from g3b1_data import tg_db
from g3b1_data.model import G3Module, G3Command
from g3b1_log.log import cfg_logger
from g3b1_serv.str_utils import uncapitalize

logger = cfg_logger(logging.getLogger(__name__), logging.WARN)


def extract_ele_members(ent_type: type) -> list[tuple[str, Any]]:
    mebrs_tup_li: list[tuple] = inspect.getmembers(ent_type)
    ele_mebrs_tup_li = [i for i in mebrs_tup_li if i[0][:2] != '__' and not inspect.isfunction(i[1])]
    return ele_mebrs_tup_li


def str_uncapitalize(s: str) -> str:
    return uncapitalize(s)


def g3_cmd_by_func(cmd_func) -> G3Command:
    split = str(cmd_func.__module__).split(".")
    func_module_str = split[len(split) - 2]
    if 'generic_hdl' in split:
        func_module_str = 'generic'
    if func_module_str.endswith('tg_hdl') and func_module_str.find('__') > -1:
        func_s_li = func_module_str.split('__')
        func_module_str = func_s_li[0]
    g3_m_str = func_module_str
    g3_m: G3Module = sel_g3_m(g3_m_str)
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


def print_header_line(text: str):
    print("".ljust(80, "="))
    print(f'=== {text.upper()} '[:76].ljust(76) + ' ===')
    print("".ljust(80, "="))


def build_debug_str(update: Update) -> str:
    return f'Your chat id is <code>{update.effective_chat.id}</code>.\n' \
           f'Your user id is <code>{update.effective_user.id}</code>.\n'


def utc_to_vn_dt(utc_dt: datetime) -> datetime:
    vn_dt = utc_dt + timedelta(hours=7)
    return vn_dt


def utc_to_vn_dt_s(utc_dt: datetime) -> str:
    return utc_to_vn_dt(utc_dt).strftime('%Y-%m-%d %H:%M:%S')


def now_for_sql() -> str:
    # datetime object containing current date and time
    now = datetime.now()
    # The sqlite datetime() function returns "YYYY-MM-DD HH:MM:SS
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
    return dt_string


def now_for_fl() -> str:
    # datetime object containing current date and time
    now = datetime.now()
    # YYYYMMDD-HHMMSS 20220207-050301
    dt_string = now.strftime("%Y%m%d-%H%M%S")
    return dt_string


def tst_for_sql() -> str:
    # datetime object containing current date and time
    now = datetime.now()
    # The sqlite datetime() function returns "YYYY-MM-DD HH:MM:SS.mmmmmmm
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S.%f")
    return dt_string


def upd_extract_chat_user_id() -> (int, int):
    return G3Ctx.chat_id(), G3Ctx.for_user_id()


def read_latest_cmd(g3_m: G3Module) -> Message:
    return read_latest_message(is_cmd_explicit=True, g3_m=g3_m)


def read_latest_message(is_cmd_explicit=False, g3_m: G3Module = None, user_id: int = 0) -> Message:
    g3m_str = g3_m.name if g3_m else ''
    if not user_id:
        user_id = G3Ctx.for_user_id()
    row: Row = tg_db.read_latest_message(G3Ctx.chat_id(), user_id, is_cmd_explicit, g3m_str).result
    if not row or not row['tg_user_id']:
        # noinspection PyTypeChecker
        return None
    dt_object = datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S')
    message = Message(row['ext_id'], dt_object, row['tg_chat_id'],
                      row['tg_user_id'], text=row['text'])
    return message


def is_msg_w_cmd(text: str = None) -> bool:
    if not text:
        # uff, i dont know
        return True
    return text.startswith('.') or text.startswith('/')
