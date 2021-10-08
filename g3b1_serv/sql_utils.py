import html

from sqlalchemy.engine import Row
from sqlalchemy.sql import ColumnElement

from generic_mdl import TgTable, TgColumn, TableDef, TgRow, COL_POS


def sql_rs_2_tbl(row_li: list[Row], columns: list[ColumnElement], tbl_name: str) -> TgTable:
    """Note: Does not work if labels are used. Try repl_dct: dict[ColumnElement, str]"""
    # noinspection PyTypeChecker
    col_li: list[TgColumn] = [TgColumn(c.key, idx + 1, c.key) for idx, c in enumerate(columns)]
    all_col_width = 0
    for col in col_li:
        val_li: list[str] = [str(row[col.key]) for row in row_li if row[col.key]]
        cut_time_suffix = True
        same_len = True
        for val in val_li:
            len_val = len(val)
            if col.width < 0:
                col.width = len_val
            if same_len and col.width != len_val:
                same_len = False
            if not same_len:
                if len_val > col.width:
                    col.width = len_val
                continue
            if cut_time_suffix:
                if len_val != 19 or val[10:] != ' 00:00:00':
                    cut_time_suffix = False
        if same_len:
            col.fix_width = True
            if cut_time_suffix and col.width == 19:
                col.width = 10
        all_col_width += col.width

    if all_col_width > 121:
        for col in col_li:
            if col.width > 13:
                col.width = 13
    tbl_def = TableDef(col_li, tbl_name)
    dict_li: list[dict] = []
    for row in row_li:
        row_dct: dict = {}
        for k, v in row.items():
            row_dct[k] = v
        dict_li.append(row_dct)
    return row_li_2_tbl(dict_li, tbl_def)


def row_li_2_tbl(row_li: list[dict], tbl_def: TableDef) -> TgTable:
    tbl: TgTable = TgTable(tbl_def, key=tbl_def.key, col_li=tbl_def.col_li)
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


def dc_dic_2_tbl(dc_dic: dict, tbl_def: TableDef) -> TgTable:
    row_li: list[dict[str, str]] = []
    for k, v in dc_dic.items():
        val_dic: dict
        if type(v) is dict:
            val_dic = v
        else:
            val_dic = v.as_dict_ext()
        row_li.append(val_dic)
    return row_li_2_tbl(row_li, tbl_def)


def tbl_2_li_str(tbl: TgTable, step=100) -> list[str]:
    str_li: list[str] = []
    row_2 = step
    while (row_2 - step) < len(tbl.row_li):
        str_li.append(tbl_2_str(tbl, row_2 - step, row_2))
        row_2 += step
    return str_li


def tbl_2_str(tbl: TgTable, idx_from=0, idx_to=-1) -> str:
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
            cel_val = html.unescape(cel_val)
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
