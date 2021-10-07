import importlib
import logging
from dataclasses import dataclass, field
from functools import cache

from elements import ELE_TY_li, EleTy
from entities import EntTy, ENT_TY_li
from g3b1_log.log import cfg_logger

logger = cfg_logger(logging.getLogger(__name__), logging.WARN)


@dataclass
class TableDef:
    col_li: list["TgColumn"]
    key: str = 'default'


@dataclass
class TgColumn:
    key: str
    pos: int
    col_name: str
    width: int = -1
    fix_width = False
    cel_li: list = field(default_factory=list)

    @staticmethod
    def contains_col_with(col_li: list["TgColumn"], key: str) -> bool:
        try:
            if TgColumn.col_by(col_li, key):
                return True
        except KeyError:
            pass
        return False

    @staticmethod
    def col_by(col_li: list["TgColumn"], key: str) -> "TgColumn":
        one_col_li = [k for k in col_li if k.key == key]
        if not one_col_li:
            raise KeyError(f'col_li does not contain a TgColumn with the key {key}!')
        assert (len(one_col_li) == 1)
        return one_col_li[0]

    @staticmethod
    def is_allow_col_with(col_li: list["TgColumn"], key: str) -> bool:
        """Col with key is allowed if either col_li is empty or col_li contains col with key"""
        if not col_li or len(col_li) < 1:
            return True
        return TgColumn.contains_col_with(col_li, key)


@dataclass
class TgTable:
    tbl_def: TableDef = TableDef([])
    key: str = 'default'
    col_li: list["TgColumn"] = field(default_factory=list)
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


@cache
def get_ele_ty_li(g3_m_str_inp: [str, list[str]]) -> list[EleTy]:
    g3_m_str_li: list[str]
    if isinstance(g3_m_str_inp, str):
        if g3_m_str_inp == 'generic':
            # noinspection PyTypeChecker
            return None
        g3_m_str_li = [g3_m_str_inp]
    else:
        g3_m_str_li = g3_m_str_inp
    ele_ty_li = [i for i in ELE_TY_li]
    for g3_m_str in g3_m_str_li:
        modu_db = importlib.import_module(f'{g3_m_str}.data.model')
        g3_m_ele_ty_li = getattr(modu_db, f'ELE_TY_{g3_m_str}_li')
        ele_ty_li.extend(g3_m_ele_ty_li)
    return ele_ty_li


def get_ent_ty_li(g3_m_str_inp: [str, list[str]]) -> list[EntTy]:
    g3_m_str_li: list[str]
    if isinstance(g3_m_str_inp, str):
        if g3_m_str_inp == 'generic':
            # noinspection PyTypeChecker
            return None
        g3_m_str_li = [g3_m_str_inp]
    else:
        g3_m_str_li = g3_m_str_inp
    ent_ty_li = [i for i in ENT_TY_li]
    for g3_m_str in g3_m_str_li:
        modu_db = importlib.import_module(f'{g3_m_str}.data.model')
        g3_m_ent_ty_li = getattr(modu_db, f'ENT_TY_{g3_m_str}_li')
        ent_ty_li.extend(g3_m_ent_ty_li)
    return ent_ty_li


def ent_ty_by_tbl_name(tbl_name: str, g3_m_str) -> "EntTy":
    for ent in get_ent_ty_li(g3_m_str):
        if ent.tbl_name == tbl_name:
            return ent


def ele_ty_by_ent_ty(ent_ty: EntTy) -> "EleTy":
    for ele in get_ele_ty_li(ent_ty.g3_m_str):
        if ele.ent_ty == ent_ty:
            return ele
