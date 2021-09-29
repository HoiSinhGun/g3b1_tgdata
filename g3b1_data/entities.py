from typing import Optional, TypeVar, Generic

G3_M_TRANS = 'trans'
G3_M_MONEY = 'money'
G3_M_SUBSCRIBE = 'subscribe'


def id_extract(ent_li: list) -> list[int]:
    return [i.id for i in ent_li]


ET = TypeVar('ET')


class EntTy(Generic[ET]):

    @staticmethod
    def by_tbl_name(tbl_name: str) -> "EntTy":
        for ent in ENT_TY_li:
            if ent.tbl_name == tbl_name:
                return ent

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

    def __init__(self, g3_m_str: str, id_: str, descr: str, tbl_name: str = '', type_: str = '') -> None:
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


print('initializing ENT_TY_LI')
ENT_TY_li = []

ENT_TY_tst_tplate = EntTy(G3_M_TRANS, 'tst_tplate', 'Test Template')
ENT_TY_tst_tplate_it = EntTy(G3_M_TRANS, 'tst_tplate_it', 'Test Item')
ENT_TY_tst_tplate_it_ans = EntTy(G3_M_TRANS, 'tst_tplate_it_ans', 'Test Answer')
ENT_TY_tst_run = EntTy(G3_M_TRANS, 'tst_run', 'Tst Run')
ENT_TY_tst_run_act = EntTy(G3_M_TRANS, 'tst_run_act', 'Tst Run Act')
ENT_TY_tst_run_act_sus = EntTy(G3_M_TRANS, 'txt_run_act_sus', 'TstRun ActSus')
ENT_TY_txt_seq = EntTy(G3_M_TRANS, 'txt_seq', 'Text Sequence', tbl_name='p_txt_seq')
ENT_TY_txt_seq_it = EntTy(G3_M_TRANS, 'txt_seq_it', 'Txt Seq Item')
ENT_TY_txtlc = EntTy(G3_M_TRANS, 'txtlc', 'Text in LC')
ENT_TY_txtlc_mp = EntTy(G3_M_TRANS, 'txtlc_mp', 'Text in LC Mapping')
ENT_TY_txtlc_onym = EntTy(G3_M_TRANS, 'txtlc_onym', 'Syn/Ant-onym')

ENT_TY_trans_li = [ENT_TY_tst_tplate, ENT_TY_tst_tplate_it, ENT_TY_tst_tplate_it_ans,
                   ENT_TY_tst_run, ENT_TY_tst_run_act, ENT_TY_tst_run_act_sus,
                   ENT_TY_txt_seq, ENT_TY_txt_seq_it,
                   ENT_TY_txtlc, ENT_TY_txtlc_mp, ENT_TY_txtlc_onym]
ENT_TY_li.extend(ENT_TY_trans_li)


class EntId(Generic[ET]):

    def __init__(self, ent_ty: EntTy[ET], id_: int) -> None:
        super().__init__()
        self.ent_ty = ent_ty
        self.id = id_
