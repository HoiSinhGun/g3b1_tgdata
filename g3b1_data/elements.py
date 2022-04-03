# noinspection PyUnresolvedReferences
import functools
from dataclasses import dataclass, field
from typing import Generic, Union, Optional

from g3b1_data.entities import EntTy, ET


@dataclass
class EleTy:
    id_: str
    descr: str
    col_name: str = ''
    type: type = None
    ent_ty: EntTy = None
    ui_len: int = -1
    ele_ty_tup: tuple = None
    key_li: list[dict[str, str]] = field(init=False, repr=False, compare=False)

    @staticmethod
    def by_col_name(col_name: str) -> "EleTy":
        for ele in ELE_TY_li:
            if ele.col_name == col_name:
                return ele

    @staticmethod
    def by_id(id_: str) -> "EleTy":
        for ele in ELE_TY_li:
            if ele.id_ == id_:
                return ele

    @staticmethod
    def by_ent_ty(ent_ty: EntTy, ele_ty_li: list["EleTy"] = None) -> "EleTy":
        if ele_ty_li is None:
            ele_ty_li = ELE_TY_li
        for ele in ele_ty_li:
            if ele.ent_ty == ent_ty:
                return ele

    def __post_init__(self) -> None:
        self.key_li = []
        if not self.col_name:
            self.col_name = self.id_
        if not self.type:
            if self.id_.endswith('_id'):
                self.type = int
            else:
                self.type = str

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __hash__(self) -> int:
        return hash(self.id_)


class EleVal(Generic[ET]):

    def __init__(self, ele_ty: EleTy, val: Union[int, str, tuple[str, ...]] = '') -> None:
        super().__init__()
        self.ele_ty = ele_ty
        self.val = val
        self.val_mp: Optional[ET] = None


class EntEleTy:
    """For all EntEleTy of a given EntTy the name must be unique."""

    def __init__(self, ent_ty: EntTy, ele_ty: EleTy, name: str = '') -> None:
        super().__init__()
        self.ent_ty = ent_ty
        self.ele_ty = ele_ty
        if name:
            self.name = name
        else:
            self.name = ele_ty.id_


ELE_TY_bkey = EleTy(id_='bkey', descr='B-Key', ui_len=20)
ELE_TY_descr = EleTy(id_='descr', descr='Description', ui_len=20)
ELE_TY_txt = EleTy(id_='txt', descr='Text', ui_len=20)
ELE_TY_sel_idx_rng = EleTy(id_='sel_idx_rng', descr='Idx Range', ui_len=10)
ELE_TY_amnt = EleTy(id_='amnt', descr='Amount', ui_len=13, type=int)
ELE_TY_area = EleTy(id_='area', descr='Area', ui_len=13)
ELE_TY_tst_type = EleTy(id_='tst_type', descr='Type', ui_len=10)
ELE_TY_su__user_id = EleTy(id_='su__user_id', descr='SU User', ui_len=10)
ELE_TY_user_id = EleTy(id_='user_id', descr='User', col_name='tg_user_id', ui_len=10)

ELE_TY_ins_tst = EleTy(id_='ins_tst', descr='Insert TST', ui_len=23)
ELE_TY_stop_tst = EleTy(id_='stop_tst', descr='Stop TST', ui_len=23)

ELE_TY_lc = EleTy(id_='lc', descr='LC', ui_len=2)
ELE_TY_lc2 = EleTy(id_='lc2', descr='L2', col_name='lc2', ui_len=2)
ELE_TY_lc_pair = EleTy(id_='lc_pair', descr='LC-L2', ui_len=5, ele_ty_tup=(ELE_TY_lc, ELE_TY_lc2))
ELE_TY_out__chat_id = EleTy(id_='out__chat_id', descr='Out Chat', ui_len=10)
ELE_TY_chat_id = EleTy(id_='chat_id', descr='Chat', col_name='tg_chat_id', ui_len=10)
ELE_TY_cmd = EleTy(id_='cmd', descr='Command', ui_len=10)
ELE_TY_cmd_prefix = EleTy(id_='cmd_prefix', descr='Cmd Pfx', ui_len=10)
ELE_TY_send_onyms = EleTy(id_='send_onyms', descr='Send Onyms', type=bool, ui_len=1)
ELE_TY_tst_mode = EleTy(id_='tst_mode', descr='tst Mode', type=int, ui_len=1)
ELE_TY_tst_mode.key_li = [dict(key='tst_mode_ed', descr='Admin: insert and update tests'),
                          dict(key='tst_mode_exe', descr='Student: take the test')]

ELE_TY_li = [ELE_TY_bkey, ELE_TY_tst_type, ELE_TY_sel_idx_rng,
             ELE_TY_txt, ELE_TY_descr, ELE_TY_amnt,
             ELE_TY_area,
             ELE_TY_lc, ELE_TY_lc2, ELE_TY_lc_pair,
             ELE_TY_user_id, ELE_TY_chat_id, ELE_TY_su__user_id, ELE_TY_out__chat_id,
             ELE_TY_cmd, ELE_TY_cmd_prefix, ELE_TY_send_onyms,
             ELE_TY_tst_mode]
