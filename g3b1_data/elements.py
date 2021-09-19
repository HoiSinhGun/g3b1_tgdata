# noinspection PyUnresolvedReferences
from dataclasses import dataclass, field
from typing import Any

from entities import *
from trans.data.enums import Lc


@dataclass
class Element:
    id_: str
    descr: str
    col_name: str = ''
    type: type = None
    ent_ty: EntTy = None
    ui_len: int = -1
    key_li: list[dict[str, str]] = field(init=False, repr=False, compare=False)

    @staticmethod
    def by_col_name(col_name: str) -> "Element":
        for ele in ELE_TY_li:
            if ele.col_name == col_name:
                return ele

    @staticmethod
    def by_ent_ty(ent_ty: EntTy) -> "Element":
        for ele in ELE_TY_li:
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


@dataclass
class EleVal:
    ele: Element
    val: Any = None
    val_mp: Any = None


ELE_TY_bkey = Element(id_='bkey', descr='B-Key', ui_len=20)
ELE_TY_descr = Element(id_='descr', descr='Description', ui_len=20)
ELE_TY_tst_type = Element(id_='tst_type', descr='Type', ui_len=10)
ELE_TY_user_id = Element(id_='user_id', descr='User', col_name='tg_user_id', ui_len=10)
ELE_TY_lc = Element(id_='lc', descr='LC', ui_len=2, type=Lc)
ELE_TY_lc2 = Element(id_='lc2', descr='L2', col_name='lc2', type=Lc, ui_len=2)
ELE_TY_chat_id = Element(id_='chat_id', descr='Chat', col_name='tg_chat_id', ui_len=10)
ELE_TY_cmd = Element(id_='cmd', descr='Command', ui_len=10)
ELE_TY_cmd_prefix = Element(id_='cmd_prefix', descr='Cmd Pfx', ui_len=10)
ELE_TY_send_onyms = Element(id_='send_onyms', descr='Send Onyms', type=bool, ui_len=1)
ELE_TY_txtlc_id = Element(id_='txtlc_id', descr='Text in LC', ent_ty=ENT_TY_txtlc)
ELE_TY_txtlc_mp_id = Element(id_='txtlc_mp_id', descr='Txtlc Map', ent_ty=ENT_TY_txtlc_mp)
ELE_TY_txt_seq_id = Element(id_='txt_seq_id', col_name='p_txt_seq_id', descr='Text Sequence', ent_ty=ENT_TY_txt_seq)
ELE_TY_txt_seq_it_id = Element(id_='txt_seq_it_id', descr='Txt Seq Item', ent_ty=ENT_TY_txt_seq_it)
ELE_TY_tst_run_id = Element(id_='tst_run_id', descr='Test Run', ent_ty=ENT_TY_tst_run)
ELE_TY_tst_run_act_id = Element(id_='tst_run_act_id', descr='TstRun Act', ent_ty=ENT_TY_tst_run_act)
ELE_TY_tst_run_act_sus_id = Element(id_='tst_run_act_sus_id', descr='TstRun ActSus', ent_ty=ENT_TY_tst_run_act_sus)
ELE_TY_tst_tplate_id = Element(id_='tst_tplate_id', descr='Test Template', ent_ty=ENT_TY_tst_tplate)
ELE_TY_tst_tplate_it_id = Element(id_='tst_tplate_it_id', descr='Tst TPlate Item', ent_ty=ENT_TY_tst_tplate_it)
ELE_TY_tst_tplate_it_ans_id = Element(id_='tst_tplate_it_ans_id', descr='Tst TP It Answer',
                                      ent_ty=ENT_TY_tst_tplate_it_ans)
ELE_TY_tst_mode = Element(id_='tst_mode', descr='tst Mode', type=int, ui_len=1)
ELE_TY_tst_mode.key_li = [dict(key='tst_mode_ed', descr='Admin: insert and update tests'),
                          dict(key='tst_mode_exe', descr='Student: take the test')]

ELE_TY_li = [ELE_TY_bkey, ELE_TY_tst_type,
             ELE_TY_descr,
             ELE_TY_lc, ELE_TY_lc2,
             ELE_TY_user_id, ELE_TY_chat_id,
             ELE_TY_cmd, ELE_TY_cmd_prefix, ELE_TY_send_onyms,
             ELE_TY_txtlc_id, ELE_TY_txtlc_mp_id,
             ELE_TY_txt_seq_id, ELE_TY_txt_seq_it_id,
             ELE_TY_tst_tplate_id, ELE_TY_tst_tplate_it_id, ELE_TY_tst_tplate_it_ans_id,
             ELE_TY_tst_run_id, ELE_TY_tst_run_act_id, ELE_TY_tst_run_act_sus_id,
             ELE_TY_tst_mode]
