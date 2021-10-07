import logging
from pydoc import html
from typing import Any

from telegram import Update, Message, ParseMode, InlineKeyboardMarkup

from g3b1_cfg.tg_cfg import G3Ctx
from g3b1_data.elements import EleTy
from g3b1_data.model import G3Result
from g3b1_serv.generic_mdl import TgTable
from g3b1_serv.sql_utils import row_li_2_tbl, dc_dic_2_tbl, tbl_2_str
from str_utils import bold, code

TIMEOUT = 30.0


def cmd_success(upd: Update):
    upd.effective_message.reply_html(
        f'Command successful!'
    )


def main():
    pass


if __name__ == '__main__':
    main()


def no_data(update: Update) -> None:
    update.effective_message.reply_html(
        'No data.'
    )
    return


def err_req_reply_to_msg(upd: Update):
    upd.effective_message.reply_html('Please reply to a message!')
    return


def cmd_p_req(upd: Update, param: str, position=1):
    upd.effective_message. \
        reply_html(f'Argument <b>{param}</b> at position {position} required!')
    return


def cmd_err_key_exists(upd: Update, obj_ty_descr: str, bkey: str):
    upd.effective_message.reply_html(
        f'Command failed! {obj_ty_descr} with key {bkey} already exists!'
    )


def cmd_err_key_not_found(upd: Update, obj_ty_descr: str, bkey: str):
    upd.effective_message.reply_html(
        f'Command failed! {obj_ty_descr} with key {bkey} not found!'
    )


def cmd_err_setng_miss(element: EleTy):
    reply(G3Ctx.upd,
          f'Command failed! Setting: {element.id_} is missing!'
          )


# def cmd_entity_by_key_not_found(upd: Update)
def cmd_err(upd: Update):
    upd.effective_message.reply_html(
        f'Command failed!'
    )


def cmd_rt_req(upd: Update):
    upd.effective_message.reply_html(
        f'Command failed. Please reply to the message which you want to translate!'
    )


def print_msg(upd: Update, msg: Message):
    reply_string = bold(msg.date.strftime("%Y-%m-%d %H:%M:%S")) + \
                   f'\n{msg.text}'
    upd.effective_message.reply_html(reply_string, reply_to_message_id=msg.message_id)


def reply(upd: Update, reply_str: str, reply_markup: InlineKeyboardMarkup = None):
    # send(upd, reply_str)
    upd.effective_message.reply_html(reply_str, reply_markup=reply_markup,
                                     timeout=TIMEOUT)


def li_send(upd: Update, send_li: list[str], reply_markup: InlineKeyboardMarkup = None):
    # send(upd, reply_str)
    for send_str in send_li:
        send(upd, send_str)


def send(upd: Update, send_str: str, reply_markup=None):
    if reply_markup and upd.callback_query:
        query = upd.callback_query
        upd.effective_message.bot.edit_message_text(
            chat_id=upd.effective_chat.id,
            message_id=query.message.message_id,
            text=send_str, parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            timeout=TIMEOUT)

        return

    if not reply_markup:
        upd.effective_message.bot.send_message(
            G3Ctx.out_chat_id(),
            send_str, parse_mode=ParseMode.HTML,
            timeout=TIMEOUT)
    else:
        upd.effective_message.bot.send_message(
            upd.effective_chat.id,
            send_str, parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            timeout=TIMEOUT)


def send_table(upd: Update, tbl_def, row_data, pfx_str: str = ''):
    if not pfx_str:
        pfx_str = ''
    if type(row_data) == list:
        tbl: TgTable = row_li_2_tbl(row_data, tbl_def)
    else:
        tbl: TgTable = dc_dic_2_tbl(row_data, tbl_def)

    step = 10
    idx_from = 0
    while idx_from < len(tbl.row_li):
        reply_str = pfx_str + f'<code>{tbl_2_str(tbl, idx_from, idx_from + step)}</code>'
        send(upd, reply_str)
        # upd.effective_message.reply_html(reply_str)
        idx_from = idx_from + step


def hdl_retco(upd: Update, logto: logging.Logger, g3r: G3Result):
    if not g3r or g3r.retco != 0:
        logto.error(f'retco: {g3r.retco}')
        cmd_err(upd)
        return

    cmd_success(upd)
    return


def send_settings(upd: Update, setng_dct: dict[str, Any]):
    reply_str = '\n'
    k_max, v_max = max_lengths(setng_dct)
    for k, v in setng_dct.items():
        if k == 'ele_ty':
            v = v.id_
        if not v:
            v = ''
        reply_str += f'{k.rjust(k_max)} = {str(v).ljust(v_max)}\n'
    reply(upd, code(html.escape(reply_str)))


def max_lengths(kv_dct: dict) -> (int, int):
    k_max: int = 0
    v_max: int = 0
    for k, v in kv_dct.items():
        if k == 'ele_id':
            v = v['id_']
        if len(k) > k_max:
            k_max = len(k)
        v_len = 20
        if isinstance(v, str):
            v_len = len(v)
        if v_len > v_max:
            v_max = v_len
    return k_max, v_max
