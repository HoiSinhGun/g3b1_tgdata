import importlib
from _ast import FunctionDef

from sqlalchemy import MetaData, Table
from sqlalchemy.engine import Engine, Result, Row
from sqlalchemy.sql import Select
from telegram import Update

import tg_reply
import tgdata_main
import utilities
from elements import EleVal
from entities import EntTy
from generic_mdl import TgColumn, TableDef, TgTable
from model import g3_m_dct, G3Command, G3Module, g3m_str_by_file_str


@tgdata_main.tg_handler()
def cmd_ent_ty_33_li(upd: Update, ent_ty: EntTy):
    meta_data: MetaData = getattr(
        importlib.import_module(f'{ent_ty.g3_m_str}.data'), f'MetaData_{ent_ty.g3_m_str.upper()}'
    )
    engine: Engine = getattr(
        importlib.import_module(f'{ent_ty.g3_m_str}.data'), f'Engine_{ent_ty.g3_m_str.upper()}'
    )
    ent_type = getattr(
        importlib.import_module(f'{ent_ty.g3_m_str}.data.model'), f'{ent_ty.type}_'
    )
    ele_mebrs_tup_li = utilities.extract_ele_members(ent_type)

    ent_r_li: list = []
    with engine.begin() as con:
        tbl: Table = meta_data.tables[ent_ty.tbl_name]
        sel: Select = tbl.select()
        r: Result = con.execute(sel)
        row_li: list[Row] = r.fetchall()
        for row in row_li:
            ent_r = ent_type.from_row(row)
            ent_r_li.append(ent_r)

    col_li: list[TgColumn] = []
    for tup in ele_mebrs_tup_li:
        id_ = tup[1].ele.id_
        position = ent_type.col_order_li().index(id_) + 1
        col_li.append(
            TgColumn(id_, position, tup[1].ele.col_name, tup[1].ele.ui_len)
        )
    tbl_def = TableDef(col_li)

    val_dct_li: list[dict] = []
    for ent_r in ent_r_li:
        ele_mebrs_tup_li = utilities.extract_ele_members(ent_r)
        val_dct: dict = {}
        for i in [i for i in ele_mebrs_tup_li if isinstance(i[1], EleVal)]:
            if i[1].val_mp:
                val_dct[i[0]] = i[1].val_mp
            else:
                val_dct[i[0]] = i[1].val
        val_dct_li.append(val_dct)

    tg_reply.send_table(upd, tbl_def, val_dct_li, '')


def init_g3_m_dct():
    if g3m_str_by_file_str(__file__) not in g3_m_dct.keys():
        g3_m: G3Module = G3Module(__file__)
        g3_m_dct[g3_m.name] = g3_m
        g3_m.cmd_dct = {}

        func_def: FunctionDef = utilities.read_function(__file__,
                                                        cmd_ent_ty_33_li.__name__)
        g3_cmd: G3Command = G3Command(g3_m, cmd_ent_ty_33_li,
                                      func_def.args.args)
        g3_m.cmd_dct['ent_ty_33_li'] = g3_cmd

init_g3_m_dct()
