import importlib
import logging
from typing import Any, Callable

from sqlalchemy import select, Column, ForeignKey, text, MetaData
from sqlalchemy.engine import Row, CursorResult, Engine, Result
from sqlalchemy.engine.mock import MockConnection
from sqlalchemy.sql import Select

from entities import *
from g3b1_log.log import cfg_logger

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def ref_cascade(ent_r) -> list[Table]:
    tbl_li: list[Table] = []
    for ent_child_r in ent_r.cascade():
        tbl_li.extend(ref_cascade(ent_child_r))
    tbl_li.extend(ref(ent_r))
    return tbl_li


def engine_by_ent_ty(ent_ty: EntTy) -> Engine:
    engine: Engine = getattr(
        importlib.import_module(f'{ent_ty.g3_m_str}.data'), f'Engine_{ent_ty.g3_m_str.upper()}'
    )
    return engine


def meta_by_ent_ty(ent_ty: EntTy) -> MetaData:
    meta_data: MetaData = getattr(
        importlib.import_module(f'{ent_ty.g3_m_str}.data'), f'MetaData_{ent_ty.g3_m_str.upper()}'
    )
    return meta_data


def ref(ent_r) -> list[Table]:
    ent_ty: EntTy = ent_r.ent_ty()
    meta: MetaData = meta_by_ent_ty(ent_ty)
    engine: Engine = engine_by_ent_ty(ent_ty)

    tbl_li: list[Table] = []

    ref_tbl_dct: dict[Table, list[str]] = ent_ty.ref_tbl_dct(meta)

    with engine.begin() as con:
        # ent_ty_tbl: Table = .tables[ent_ty.tbl_name]
        # col_sfx = f'{ent_ty.tbl_name}_id'
        for tbl, col_id_li in ref_tbl_dct.items():
            for col_id in col_id_li:
                logger.debug(f'{tbl} - {col_id}')
                if 'id' in tbl.c.keys():
                    sql_stmnt: Select = select(tbl.c.id)
                else:
                    sql_stmnt: Select = select([text(f'ROWID')])
                sql_stmnt = sql_stmnt.where(tbl.c[col_id] == ent_r.id_).limit(1)
                rs: Result = con.execute(sql_stmnt)
                fk_ref_row: Row = rs.first()
                if fk_ref_row:
                    tbl_li.append(tbl)
                    break
    return tbl_li


def orm(con: MockConnection, tbl: Table, row: Row, from_row_any: Callable, repl_dct=None) -> dict[str, Any]:
    if repl_dct is None:
        repl_dct = {}
    col: Column
    for col_id, col in tbl.columns.items():
        if col_id in repl_dct.keys():
            continue
        fk: ForeignKey
        for fk in col.foreign_keys:
            if fk.column.key != 'id':
                logger.error('foreign key target is not a column with the name "id"')
                continue
            fk_tbl: Table = fk.column.table
            sql_stmnt: Select = select(fk_tbl)
            fk_ref_col_val = row[col_id]
            if not fk_ref_col_val:
                repl_dct[col_id] = None
                break

            if not isinstance(fk_ref_col_val, int):
                break

            sql_stmnt = sql_stmnt.where(fk_tbl.columns.id == int(fk_ref_col_val))
            rs: CursorResult = con.execute(sql_stmnt)
            fk_ref_row: Row = rs.first()
            ent_ty = EntTy.by_tbl_name(fk_tbl.name)
            repl_dct[col_id] = from_row_any(ent_ty, fk_ref_row)
            break
    return repl_dct
