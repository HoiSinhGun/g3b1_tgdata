import importlib
from typing import Optional, TypeVar, Generic, Callable, Union

from sqlalchemy import MetaData
from sqlalchemy.engine import Engine

G3_M_TRANS = 'trans'
G3_M_MONEY = 'money'
G3_M_SUBSCRIBE = 'subscribe'


def id_extract(ent_li: list) -> list[int]:
    return [i.id for i in ent_li]


ET = TypeVar('ET')


class EntTy(Generic[ET]):

    @staticmethod
    def by_id(id_: str) -> "EntTy":
        if id_.find(':') > 0:
            id_ = id_.split(':')[1]
        for ent in ENT_TY_li:
            if ent.id == id_:
                return ent

    @staticmethod
    def by_cmd_prefix(cmd_prefix: str) -> Optional["EntTy"]:
        if not cmd_prefix:
            return
        for ent in ENT_TY_li:
            if ent.cmd_prefix == cmd_prefix:
                return ent

    def __init__(self, g3_m_str: str, id_: str, descr: str, tbl_name: str = '', type_: str = '',
                 sel_ent_ty='', it_ent_ty_dct: dict[str, "EntTy"] = None) -> None:
        super().__init__()
        self.g3_m_str: str = g3_m_str
        self.id: str = id_
        self.descr: str = descr
        if tbl_name:
            self.tbl_name: str = tbl_name
        else:
            self.tbl_name = self.id
        if type_:
            self.type: str = type_
        else:
            self.type = ''
            for i in self.id.split('_'):
                self.type += i.capitalize()
        self.sel_ent_ty = sel_ent_ty
        if it_ent_ty_dct:
            self.it_ent_ty_dct = it_ent_ty_dct
        else:
            self.it_ent_ty_dct = {}

        self.cmd_prefix = ''
        self.but_cmd_def = ''
        self.but_cmd_li = []
        self.keyboard_descr = ''
        self.ref_tbl_dct = None
        self.ele_ty_dct = None

    def get_cmd_by_but(self, text: str) -> str:
        but_tup_li = [but_tup for but_tup_li in self.but_cmd_li for but_tup in but_tup_li if but_tup[0] == text]
        if not but_tup_li:
            return f'{self.cmd_prefix}{self.but_cmd_def} {text}'
        return self.cmd_prefix + but_tup_li[0][1]

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __hash__(self) -> int:
        return hash(self.id)


print('initializing ENT_TY_LI')
ENT_TY_li = []


class EntId(Generic[ET]):

    def __init__(self, ent_ty: EntTy[ET], id_: Union[int, str], g3_bot_id: int = None) -> None:
        super().__init__()
        self.ent_ty = ent_ty
        self.id = id_
        self.g3_bot_id = g3_bot_id


def get_meta_attr(ent_ty: EntTy) -> (Callable, MetaData, Engine):
    from_row_any: Callable = getattr(
        importlib.import_module(f'{ent_ty.g3_m_str}.data.integrity'), 'from_row_any'
    )
    md: MetaData = getattr(
        importlib.import_module(f'{ent_ty.g3_m_str}.data'), f'md_{ent_ty.g3_m_str.upper()}'
    )
    eng: Engine = getattr(
        importlib.import_module(f'{ent_ty.g3_m_str}.data'), f'eng_{ent_ty.g3_m_str.upper()}'
    )
    return from_row_any, md, eng
