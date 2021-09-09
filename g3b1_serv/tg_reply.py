from pydoc import html
from typing import Any

from elements import Element
from g3b1_serv.utilities import *


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
        'No g3b1_data found. Try /create <title/bkey>'
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


def cmd_err_setng_miss(upd: Update, ELE_TY: Element):
    upd.effective_message.reply_html(
        f'Command failed! Setting: {ELE_TY.id_} is missing!'
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


def reply(upd: Update, reply_str: str):
    upd.effective_message.reply_html(reply_str)


def send_table(upd: Update, tbl_def, row_data, pfx_str: str):
    if not pfx_str:
        pfx_str = ''
    if type(row_data) == list:
        tbl: TgTable = row_li_to_table(row_data, tbl_def)
    else:
        tbl: TgTable = dc_dic_to_table(row_data, tbl_def)

    step = 20
    idx_from = 0
    while idx_from < len(tbl.row_li):
        reply_str = pfx_str + f'<code>{table_print(tbl, idx_from, idx_from + step)}</code>'
        upd.effective_message.reply_html(reply_str)
        idx_from = idx_from + step


def code(text: str) -> str:
    return f'<code>{text}</code>'


def bold(text: str) -> str:
    return f'<b>{text}</b>'


def italic(text: str) -> str:
    return f'<i>{text}</i>'


def send_settings(upd: Update, setng_dct: dict[str, Any]):
    reply_str = '\n'
    k_max, v_max = max_lengths(setng_dct)
    for k, v in setng_dct.items():
        if k == 'ele_id':
            v = v['id']
        reply_str += f'{k.rjust(k_max)} = {str(v).ljust(v_max)}\n'
    reply(upd, code(html.escape(reply_str)))


def max_lengths(kv_dct: dict) -> (int, int):
    k_max: int = 0
    v_max: int = 0
    for k, v in kv_dct.items():
        if k == 'ele_id':
            v = v['id']
        if len(k) > k_max:
            k_max = len(k)
        v_len = 20
        if isinstance(v, str):
            v_len = len(v)
        if v_len > v_max:
            v_max = v_len
    return k_max, v_max
