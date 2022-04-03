import importlib
import inspect
import logging
from functools import wraps
from typing import Any, Callable

from sqlalchemy import select, Column, ForeignKey, text, MetaData, Table
from sqlalchemy.engine import Connection
from sqlalchemy.engine import Row, CursorResult, Engine, Result
from sqlalchemy.sql import Select

from g3b1_cfg.tg_cfg import G3Ctx
from g3b1_data.entities import EntTy
from g3b1_log.log import cfg_logger
from generic_mdl import ent_ty_by_tbl_name

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def ref_cascade(ent_r) -> list[Table]:
    tbl_li: list[Table] = []
    for ent_child_r in ent_r.cascade():
        tbl_li.extend(ref_cascade(ent_child_r))
    tbl_li.extend(ref(ent_r))
    return tbl_li


def engine_by_ent_ty(ent_ty: EntTy) -> Engine:
    engine: Engine = getattr(
        importlib.import_module(f'{ent_ty.g3_m_str}.data'), f'eng_{ent_ty.g3_m_str.upper()}'
    )
    return engine


def meta_by_ent_ty(ent_ty: EntTy) -> MetaData:
    meta_data: MetaData = getattr(
        importlib.import_module(f'{ent_ty.g3_m_str}.data'), f'md_{ent_ty.g3_m_str.upper()}'
    )
    return meta_data


def ref_tbl_dct(ent_ty: EntTy) -> dict[Table, list[str]]:
    if ent_ty.ref_tbl_dct is not None:
        return ent_ty.ref_tbl_dct
        # noinspection PyAttributeOutsideInit
    md: MetaData = getattr(
        importlib.import_module(f'{ent_ty.g3_m_str}.data'), f'md_{ent_ty.g3_m_str.upper()}'
    )
    ent_ty.ref_tbl_dct = {}
    col_sfx = f'{ent_ty.tbl_name}_id'
    for t in md.tables:
        tbl: Table = md.tables[t]
        col_id_li = [k for k in tbl.columns.keys() if k.endswith(col_sfx)]
        if not col_id_li:
            continue
        ent_ty.ref_tbl_dct[tbl] = col_id_li
    return ent_ty.ref_tbl_dct


def ref(ent_r) -> list[Table]:
    ent_ty: EntTy = ent_r.ent_ty()
    meta: MetaData = meta_by_ent_ty(ent_ty)
    engine: Engine = engine_by_ent_ty(ent_ty)

    tbl_li: list[Table] = []

    ref_dct: dict[Table, list[str]] = ent_ty.ref_tbl_dct(meta)

    with engine.begin() as con:
        # ent_ty_tbl: Table = .tables[ent_ty.tbl_name]
        # col_sfx = f'{ent_ty.tbl_name}_id'
        for tbl, col_id_li in ref_dct.items():
            for col_id in col_id_li:
                logger.debug(f'{tbl} - {col_id}')
                if 'id' in tbl.columns().keys():
                    sql_stmnt: Select = select(tbl.columns().id)
                else:
                    sql_stmnt: Select = select([text(f'ROWID')])
                sql_stmnt = sql_stmnt.where(tbl.columns()[col_id] == ent_r.id).limit(1)
                rs: Result = con.execute(sql_stmnt)
                fk_ref_row: Row = rs.first()
                if fk_ref_row:
                    tbl_li.append(tbl)
                    break
    return tbl_li


def orm(con: Connection, tbl: Table, row: Row, from_row_any: Callable, repl_dct=None) -> dict[str, Any]:
    if repl_dct is None:
        repl_dct = {}
    col: Column
    for col_id, col in tbl.columns.items():
        if col_id in repl_dct.keys() or col_id in ['act_ty', 'sus_bkey', 'crcy']:
            continue
        fk: ForeignKey
        for fk in col.foreign_keys:
            if fk.column.key != 'id':
                logger.error(f'foreign key ({fk}) target is not a column with the name "id"')
                continue
            fk_tbl: Table = fk.column.table
            row.keys()
            if row is None:
                logger.error(f'row is None. Info: Tbl: {tbl} - FK: {fk}')
                continue
            fk_ref_col_val = row[col_id]
            if not fk_ref_col_val:
                repl_dct[col_id] = None
                break

            if not isinstance(fk_ref_col_val, int):
                break

            sql_stmnt: Select = select(fk_tbl)
            sql_stmnt = sql_stmnt.where(fk_tbl.columns.id == int(fk_ref_col_val))
            rs: CursorResult = con.execute(sql_stmnt)
            fk_ref_row: Row = rs.first()
            ent_ty = ent_ty_by_tbl_name(fk_tbl.name, [G3Ctx.g3_m_str, 'subscribe'])
            repl_dct[col_id] = from_row_any(ent_ty, fk_ref_row, {})
            break
    return repl_dct
