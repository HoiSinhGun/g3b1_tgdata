import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Callable

from telegram import Update

from log.g3b1_log import cfg_logger

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


@dataclass
class TableDef:
    cols: list
    key: str = 'default'

    def is_allow_col(self, col_name: str) -> bool:
        if not self.cols or len(self.cols) < 1:
            return True
        return col_name in self.cols


@dataclass
class TgTable:
    tbl_def: TableDef = TableDef([])
    key: str = 'default'
    col_dic: dict = field(default_factory=dict)
    row_li: list = field(default_factory=list)


@dataclass
class TgColumn:
    key: str
    pos: int
    name: str
    width: int = -1
    cel_li: list = field(default_factory=list)


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


@dataclass
class TgCommand:
    name: str
    long_name: str
    handler: Callable
    description: str
    args: list = ()

    def as_dict_ext(self) -> dict:
        values = asdict(self)
        new_dict = dict()
        for item in values.keys():
            if values[item]:
                new_dict[item] = values[item]
        return new_dict


def lod_to_dic(lod: list) -> dict:
    count: int = 1
    data_as_dic: dict = {}
    for i in lod:
        data_as_dic.update({count: i})
        count += 1
    return data_as_dic


def dc_dic_to_table(dc_dic: dict, tbl_def: TableDef) -> TgTable:
    tbl: TgTable = TgTable(tbl_def)
    count: int = 0
    # count_col: int = 0
    for k, v in dc_dic.items():
        val_dic: dict
        if type(v) is dict:
            val_dic = v
        else:
            val_dic = v.as_dict_ext()
        row: TgRow = TgRow(tbl, str(k), count + 1, [], val_dic)
        tbl.row_li.append(row)
        for k_, v_ in val_dic.items():
            if not tbl.tbl_def.is_allow_col(k_):
                continue
            if k_ in tbl.col_dic.keys():
                continue
            col: TgColumn = TgColumn(k_, tbl.tbl_def.cols.index(k_) + 1, k_, width=15)
            logger.debug(f'append col: {col}')
            tbl.col_dic.update({col.key: col})
        count += 1
    return tbl


def table_print(tbl: TgTable) -> str:
    row: TgRow
    col: TgColumn
    col_key: str
    cel_val: str
    row_str: str
    tbl_str: str = ""
    for row in tbl.row_li:
        row_str = ""
        for col_key in tbl.tbl_def.cols:
            col = tbl.col_dic[col_key]
            if col_key not in row.val_dic.keys():
                row_str = row_str + str('').ljust(col.width) + " | "
                continue
            cel_val = str(row.val_dic[col_key])
            cel_val = str(cel_val[:col.width]).ljust(col.width)
            row_str = row_str + cel_val + " | "
        tbl_str = tbl_str + f'{row_str}\n'
    row_str = ''
    row_hr = ''
    for col_key in tbl.tbl_def.cols:
        col = tbl.col_dic[col_key]
        row_hr = row_hr + str('').ljust(col.width, '_') + '___'
        row_str = row_str + str(col.name[:col.width]).ljust(col.width) + " | "
    tbl_str = f'{row_hr}\n{row_str}\n{row_hr}\n{tbl_str}{row_hr}'

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f'\n{tbl_str}')
    return tbl_str


def build_commands_str(commands: dict):
    commands_str = ''
    for key, tg_command in commands.items():
        commands_str += f'/{tg_command.long_name} {tg_command.args}: {tg_command.description}\n'
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
    print(now_for_sql())
    command = TgCommand(name='test', long_name='test', description="test", args=dict(), handler=None)
    print(command, command.name, command.args, command.handler)


if __name__ == '__main__':
    main()
