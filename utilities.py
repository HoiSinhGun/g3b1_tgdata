import ast
import inspect
import logging
import os
from ast import arg
from ast import FunctionDef
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Callable

from telegram import Update

# import subscribe_main
from log.g3b1_log import cfg_logger

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


@dataclass
class TableDef:
    cols: dict
    key: str = 'default'

    def is_allow_col(self, col_key: str) -> bool:
        if not self.cols or len(self.cols) < 1:
            return True
        return col_key in self.cols.keys()

    def col_width(self, col_key: str) -> int:
        if not self.cols or len(self.cols) < 1:
            return 15
        return self.cols[col_key].width

    def col_name(self, col_key: str) -> str:
        return self.cols[col_key].col_name


@dataclass
class TgColumn:
    key: str
    pos: int
    col_name: str
    width: int = -1
    cel_li: list = field(default_factory=list)


@dataclass
class TgTable:
    tbl_def: TableDef = TableDef({})
    key: str = 'default'
    col_dic: dict = field(default_factory=dict)
    row_li: list = field(default_factory=list)


@dataclass
class TgRow:
    tbl: TgTable
    key: str
    pos: int
    cel_li: list = field(default_factory=list)
    val_dic: dict = field(default_factory=dict)


@dataclass
class TgCell:
    col: TgColumn
    row: TgRow
    val: str


COL_POS = TgColumn('position', 0, 'Row', 4)


@dataclass
class G3Module:
    file_main: str = field(repr=False)
    li_col_dct: dict = field(repr=False)
    cmd_dct: dict = field(default=None, repr=False)
    name: str = field(init=False)
    src_code: str = field(init=False, repr=False)

    def __post_init__(self):
        self.name = module_by_file_str(self.file_main)
        with open(self.file_main, 'r') as f:
            self.src_code = f.read()


g3_m_dct = {}


def cmd_dct_by(mod_str: str) -> dict:
    return g3_m_dct[mod_str].cmd_dct


@dataclass
class G3Command:
    g3_m: G3Module
    handler: Callable
    args: list[arg]  # = field(init=False, repr=True)
    name: str = field(init=False, repr=True)
    long_name: str = field(init=False, repr=True)
    description: str = field(init=False, repr=True)

    def __post_init__(self):
        # Note: handler is not passed as an argument
        # here anymore, because it is not an
        # `InitVar` anymore.
        self.long_name = str(self.handler.__name__).replace("hdl_cmd_", "")
        self.name = self.long_name.replace(f'{self.g3_m.name}_', "")
        self.description = self.handler.__doc__

    def as_dict_ext(self) -> dict:
        values = asdict(self)
        new_dict = dict()
        for key in values.keys():
            if values[key]:
                new_dict[key] = values[key]
        return new_dict


def read_functions(py_file: str):
    filename = py_file
    with open(filename) as file:
        node = ast.parse(file.read())
    n: FunctionDef

    func_li = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name.startswith('hdl_cmd_')]

    # for function in func_li:
    #    print(function.name)
    return func_li


def initialize_g3_m_dct(g3_m_file: str, li_col_dct: dict) -> G3Module:
    g3_m = G3Module(g3_m_file, li_col_dct)
    cmd_dct = {}
    hdl: ast.FunctionDef
    hdl_li = read_functions(g3_m_file)
    for hdl in hdl_li:
        script = script_by_file_str(g3_m.file_main)
        cpl = compile(f"import {script}\n", "<string>", "exec")
        exec(cpl)
        g3_cmd = G3Command(g3_m, eval(f'{script}.{hdl.name}'), hdl.args.args)
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
    tbl: TgTable = TgTable(tbl_def, col_dic=tbl_def.cols)
    count: int = 0
    # count_col: int = 0
    for k, v in dc_dic.items():
        val_dic: dict
        if type(v) is dict:
            val_dic = v
        else:
            val_dic = v.as_dict_ext()
        row_nr = count + 1
        row: TgRow = TgRow(tbl, str(k), row_nr, [], val_dic)
        tbl.row_li.append(row)
        if COL_POS.key not in tbl.col_dic.keys():
            tbl.col_dic.update({COL_POS.key: TgColumn(COL_POS.key, COL_POS.pos, COL_POS.col_name, COL_POS.width)})
        for k_, v_ in val_dic.items():
            if not tbl.tbl_def.is_allow_col(k_):
                continue
            if k_ in tbl.col_dic.keys():
                continue
            col: TgColumn = TgColumn(k_, -1, tbl_def.col_name(k_), width=tbl_def.col_width(k_))
            # logger.debug(f'append col: {col}')
            tbl.col_dic.update({col.key: col})
        count += 1
    return tbl


def print_header_line(text: str):
    print("".ljust(80, "="))
    print(f'=== {text.upper()} '[:76].ljust(76) + ' ===')
    print("".ljust(80, "="))


def script_by_file_str(file: str) -> str:
    file_name = os.path.basename(file)
    # file name without extension
    return os.path.splitext(file_name)[0]


def module_by_file_str(file: str) -> str:
    """E.g. python script base file = subscribe_main.py => subscribe"""
    return script_by_file_str(file).split("_")[0]


def g3_cmd_by_func(func) -> G3Command:
    g3_m_str = str(func.__module__).split("_")[0]
    g3_m: G3Module = g3_m_dct[g3_m_str]
    prefix: str = f'hdl_cmd_'  # {g3_m_str}_'
    len_prefix: int = len(prefix)
    f_name = str(func.__name__)
    cmd_name = f_name[len_prefix:len(f_name)]
    g3_cmd: G3Command = g3_m.cmd_dct[cmd_name]
    return g3_cmd


def module_by_inspect() -> str:
    module = cinfo_by_inspect()[1].split("_")[0]
    logger.debug(f"module requested: {module}")
    return module


def cinfo_by_inspect() -> (str, str):
    # first get the full filename (including path and file extension)
    # print(inspect.stack())
    caller_frame = inspect.stack()[2]
    caller_filename_full = caller_frame.filename

    # now get rid of the directory (via basename)
    # then split filename and extension (via splitext)
    caller_filename_only = os.path.splitext(os.path.basename(caller_filename_full))[0]

    # return both filename versions as tuple
    return caller_filename_full, caller_filename_only


def table_print(tbl: TgTable) -> str:
    row: TgRow
    col: TgColumn
    col_key: str
    cel_val: str
    row_str: str
    tbl_str: str = ""
    for row in tbl.row_li:
        row_str = ""
        for col_key in tbl.tbl_def.cols.keys():
            col = tbl.col_dic[col_key]
            if col_key == COL_POS.key:
                cel_val = str(tbl.row_li.index(row) + 1)
            elif col_key not in row.val_dic.keys():
                row_str = row_str + str('').ljust(col.width) + " | "
                continue
            else:
                cel_val = str(row.val_dic[col_key])
            cel_val = str(cel_val[:col.width]).ljust(col.width)
            row_str = row_str + cel_val + " | "
        tbl_str = tbl_str + f'{row_str}\n'
    row_str = ''
    row_hr = ''
    for col_key in tbl.tbl_def.cols.keys():
        col = tbl.col_dic[col_key]
        row_hr = row_hr + str('').ljust(col.width, '_') + '___'
        row_str = row_str + str(col.col_name[:col.width]).ljust(col.width) + " | "
    tbl_str = f'{row_hr}\n{row_str}\n{row_hr}\n{tbl_str}{row_hr}'

    # if logger.isEnabledFor(logging.DEBUG):
    #    logger.debug(f'\n{tbl_str}')
    return tbl_str


def build_commands_str(commands: dict[str, G3Command]):
    commands_str = ''
    for key, g3_cmd in commands.items():
        args_str = '['
        for item in g3_cmd.args:
            args_str += item.arg + ', '
        args_str = args_str[:len(args_str)-2] + ']'
        commands_str += f'/{g3_cmd.long_name} {args_str}: {g3_cmd.description}\n'
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


def main():
    import subscribe_main
    g3_m_dct.update({'subscribe': initialize_g3_m_dct(subscribe_main.__file__, {})})
    print(now_for_sql())
    g3_m: G3Module = g3_m_dct['subscribe']
    g3_cmd: G3Command
    for g3_cmd_str, g3_cmd in g3_m.cmd_dct.items():
        print(g3_cmd.name, g3_cmd.description, g3_cmd.args, g3_cmd.handler)


if __name__ == '__main__':
    main()
