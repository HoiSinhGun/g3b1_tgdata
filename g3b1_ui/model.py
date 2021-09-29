from typing import Union

from telegram import Update, ReplyMarkup

from g3b1_data.elements import EntEleTy
from g3b1_serv import tg_reply
from g3b1_serv.generic_mdl import TgTable
from g3b1_serv.utilities import tbl_2_str


class TgUIC:
    """UI Connector"""
    uic: "TgUIC" = None

    def __init__(self, upd: Update) -> None:
        super().__init__()
        self.upd = upd

    def err_p_404(self, p: Union[str, id], ent_ele_ty: EntEleTy):
        """Instance for key p not found"""
        tg_reply.cmd_err_key_not_found(self.upd, ent_ele_ty.ent_ty.descr, str(p))

    def err_p_miss(self, ent_ele_ty: EntEleTy):
        tg_reply.cmd_p_req(self.upd, ent_ele_ty.name)

    def send(self, send_str: str, reply_markup: ReplyMarkup = None):
        tg_reply.send(self.upd, send_str, reply_markup)

    def no_data(self):
        tg_reply.no_data(self.upd)

    def cmd_sccs(self):
        self.send('Command Successful!')

    def cmd_fail(self):
        tg_reply.cmd_err(self.upd)

    def send_settings(self, setng_dct):
        tg_reply.send_settings(self.upd, setng_dct)

    def send_tg_tbl(self, tbl: TgTable, pfx_str='%tbl%'):
        if pfx_str == '%tbl%':
            pfx_str = tbl.key + '\n'
        step = 10
        idx_from = 0
        while idx_from < len(tbl.row_li):
            reply_str = pfx_str + f'<code>{tbl_2_str(tbl, idx_from, idx_from + step)}</code>'
            self.send(reply_str)
            # upd.effective_message.reply_html(reply_str)
            idx_from = idx_from + step
