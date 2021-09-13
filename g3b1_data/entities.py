from dataclasses import dataclass, field

from sqlalchemy import Table, MetaData

G3_M_TRANS = 'trans'


def id_extract(ent_li: list) -> list[int]:
    return [i.id for i in ent_li]


@dataclass
class EntTy:
    g3_m_str: str
    id_: str
    descr: str
    tbl_name: str = ''
    type: str = ''
    _ref_tbl_dct: dict[Table, list[str]] = field(init=False, repr=False)

    @staticmethod
    def by_tbl_name(tbl_name: str) -> "EntTy":
        for ent in ENT_TY_li:
            if ent.tbl_name == tbl_name:
                return ent

    @staticmethod
    def by_id(id_: str) -> "EntTy":
        for ent in ENT_TY_li:
            if ent.id_ == id_:
                return ent

    def __post_init__(self) -> None:
        if not self.tbl_name:
            self.tbl_name = self.id_
        if not self.type:
            self.type = ''
            for i in self.id_.split('_'):
                self.type += i.capitalize()
        # noinspection PyTypeChecker
        self._ref_tbl_dct = None

    def ref_tbl_dct(self, meta: MetaData = None) -> dict[Table, list[str]]:
        if self._ref_tbl_dct is not None:
            return self._ref_tbl_dct
        self._ref_tbl_dct = {}
        col_sfx = f'{self.tbl_name}_id'
        for t in meta.tables:
            tbl: Table = meta.tables[t]
            col_id_li = [k for k in tbl.c.keys() if k.endswith(col_sfx)]
            if not col_id_li:
                continue
            self._ref_tbl_dct[tbl] = col_id_li
        return self._ref_tbl_dct


ENT_TY_tst_tplate = EntTy(G3_M_TRANS, 'tst_tplate', 'Test Template')
ENT_TY_tst_tplate_it = EntTy(G3_M_TRANS, 'tst_tplate_it', 'Test Item')
ENT_TY_tst_tplate_it_ans = EntTy(G3_M_TRANS, 'tst_tplate_it_ans', 'Test Answer')
ENT_TY_tst_run = EntTy(G3_M_TRANS, 'tst_run', 'Tst Run')
ENT_TY_tst_run_act = EntTy(G3_M_TRANS, 'tst_run_act', 'Tst Run Act')
ENT_TY_tst_run_act_sus = EntTy(G3_M_TRANS, 'txt_run_act_sus', 'TstRun ActSus')
ENT_TY_txt_seq = EntTy(G3_M_TRANS, 'txt_seq', 'Text Sequence')
ENT_TY_txt_seq_it = EntTy(G3_M_TRANS, 'txt_seq_it', 'Txt Seq Item')
ENT_TY_txtlc = EntTy(G3_M_TRANS, 'txtlc', 'Text in LC')
ENT_TY_txtlc_mp = EntTy(G3_M_TRANS, 'txtlc_mp', 'Text in LC Mapping')
ENT_TY_txtlc_onym = EntTy(G3_M_TRANS, 'txtlc_onym', 'Syn/Ant-onym')

ENT_TY_li = [ENT_TY_tst_tplate, ENT_TY_tst_tplate_it, ENT_TY_tst_tplate_it_ans,
             ENT_TY_tst_run, ENT_TY_tst_run_act, ENT_TY_tst_run_act_sus,
             ENT_TY_txt_seq, ENT_TY_txt_seq_it,
             ENT_TY_txtlc, ENT_TY_txtlc_mp, ENT_TY_txtlc_onym]
