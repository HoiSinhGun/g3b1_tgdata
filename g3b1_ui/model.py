from typing import Union

from telegram import Update, ReplyMarkup

from g3b1_data.elements import EleTy
from g3b1_serv import tg_reply
from g3b1_serv.generic_mdl import TgTable
from sql_utils import tbl_2_str


class TgUIC:
    """UI Connector"""
    uic: "TgUIC" = None
    f_send = True
    send_str_li = []

    def __init__(self, upd: Update) -> None:
        super().__init__()
        self.upd = upd

    @classmethod
    def get_send_str_li(cls) -> list[str]:
        res_li: list[str] = list(cls.send_str_li)
        cls.send_str_li.clear()
        cls.f_send = True
        return res_li

    def err_p_404(self, p: Union[str, id], ele_ty: EleTy):
        """Instance for key p not found"""
        tg_reply.cmd_err_key_not_found(self.upd, ele_ty.ent_ty.descr, str(p))

    def err_p_miss(self, ele_ty: EleTy):
        tg_reply.cmd_p_req(self.upd, ele_ty.descr)

    def err_setng_miss(self, ele_ty: EleTy):
        self.error(f'Command failed! Setting: {ele_ty.descr} ({ele_ty.id_}) is missing!')

    def send(self, send_str: str, reply_markup: ReplyMarkup = None) -> str:
        if TgUIC.f_send:
            tg_reply.send(self.upd, send_str, reply_markup)
        else:
            TgUIC.send_str_li.append(send_str)
        return send_str

    def err_no_select(self) -> str:
        return self.error('Select an entry!')

    def no_data(self):
        tg_reply.no_data(self.upd)

    def cmd_sccs(self):
        self.send('Command Successful!')

    def err_cmd_fail(self):
        tg_reply.cmd_err(self.upd)

    def error(self, send_str) -> str:
        send_str = f'🚫 {send_str}'
        return self.send(send_str)

    def info(self, send_str):
        self.send(f'ℹ️ {send_str}')

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
