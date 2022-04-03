import logging
from pydoc import html
from time import sleep
from typing import Any, Union

from telegram import Update, Message, ParseMode, InlineKeyboardMarkup, Bot, ReplyMarkup
from telegram.error import BadRequest, RetryAfter

from trans.data.model import MenuKeyboard
from g3b1_cfg.tg_cfg import G3Ctx
from g3b1_data.elements import EleTy
from g3b1_data.model import G3Result, Menu
from g3b1_log.log import cfg_logger
from g3b1_serv.generic_mdl import TgTable
from g3b1_serv.sql_utils import row_li_2_tbl, dc_dic_2_tbl, tbl_2_str
from str_utils import bold, code
from tg_db import upd_chat_last_msg, sel_chat_last_msg, read_latest_message

TIMEOUT = 30.0

logger = cfg_logger(logging.getLogger(__name__), logging.WARN)


def reply_html(upd: Update, reply_s: str, **kwargs):
    sent_msg: Message = upd.effective_message.reply_html(reply_s, **kwargs)
    upd_chat_last_msg(sent_msg.chat_id, sent_msg.message_id)


def cmd_success(upd: Update):
    reply_html(upd,
               f'Command successful!'
               )


def main():
    pass


if __name__ == '__main__':
    main()


def no_data(update: Update) -> None:
    reply_html(update,
               'No data.'
               )
    return


def err_req_reply_to_msg(upd: Update):
    reply_html(upd, 'Please reply to a message!')
    return


def cmd_p_req(upd: Update, param: str, position=1):
    reply_html(upd, f'Argument <b>{param}</b> at position {position} required!')
    return


def cmd_err_key_exists(upd: Update, obj_ty_descr: str, bkey: str):
    reply_html(upd,
               f'Command failed! {obj_ty_descr} with key {bkey} already exists!'
               )


def cmd_err_key_not_found(upd: Update, obj_ty_descr: str, bkey: str):
    reply_html(upd,
               f'Command failed! {obj_ty_descr} with key {bkey} not found!'
               )


def cmd_err_setng_miss(element: EleTy):
    reply(G3Ctx.upd,
          f'Command failed! Setting: {element.id_} is missing!'
          )


# def cmd_entity_by_key_not_found(upd: Update)
def cmd_err(upd: Update):
    reply_html(upd,
               f'Command failed!'
               )


def cmd_rt_req(upd: Update):
    reply_html(upd,
               f'Command failed. Please reply to the message which you want to translate!'
               )


def print_msg(upd: Update, msg: Message):
    reply_string = bold(msg.date.strftime("%Y-%m-%d %H:%M:%S")) + \
                   f'\n{msg.text}'
    reply_html(upd, reply_string, reply_to_message_id=msg.message_id)


def reply(upd: Update, reply_str: str, reply_markup: InlineKeyboardMarkup = None):
    # send(upd, reply_str)
    reply_html(upd, reply_str, reply_markup=reply_markup,
               timeout=TIMEOUT)


def li_send(upd: Update, send_li: list[str], reply_markup: InlineKeyboardMarkup = None):
    for send_str in send_li:
        send(upd, send_str, menu_keyboard=reply_markup)


def send(upd: Update, send_str: str, menu_keyboard: Union[MenuKeyboard, ReplyMarkup] = None,
         upd_msg_id=0, force_new_msg=False) -> \
        Union[Message, str]:
    chat_id = upd.effective_chat.id
    bot = upd.effective_message.bot
    bot_id = bot.id
    if menu_keyboard and isinstance(menu_keyboard, MenuKeyboard):
        reply_markup: ReplyMarkup = menu_keyboard.reply_markup
        menu: Menu = menu_keyboard.menu
        latest_menu_msg = read_latest_message(chat_id, bot_id, menu_id=menu.id).result
        if latest_menu_msg:
            upd_msg_id = latest_menu_msg['ext_id']
    else:
        reply_markup: ReplyMarkup = menu_keyboard
    if reply_markup and (upd.callback_query or upd_msg_id):
        if not upd_msg_id:
            query = upd.callback_query
            upd_msg_id = query.message.message_id
        try:
            last_msg_id = sel_chat_last_msg(chat_id)
            logger.debug(f'chat_id: {chat_id}, last_msg_id: {last_msg_id}')
            if last_msg_id - upd_msg_id > 4 or force_new_msg:
                # upd.effective_message.bot.delete_message(chat_id, upd_msg_id)
                sent_msg = bot.send_message(chat_id, send_str, parse_mode=ParseMode.HTML,
                                            disable_web_page_preview=True,
                                            reply_markup=reply_markup,
                                            timeout=TIMEOUT)
            else:
                sent_msg = bot.edit_message_text(chat_id=chat_id,
                                                 message_id=upd_msg_id,
                                                 disable_web_page_preview=True, text=send_str,
                                                 parse_mode=ParseMode.HTML,
                                                 reply_markup=reply_markup,
                                                 timeout=TIMEOUT)
            upd_chat_last_msg(sent_msg.chat_id, sent_msg.message_id)
            return sent_msg
        except BadRequest as msg:
            if msg.message.startswith('Message is not modified'):
                return 'UNMODIFIED'
            logger.exception(msg)
            return 'ERROR'
        # return send_str

    if not reply_markup:
        while True:
            try:
                sent_msg = bot.send_message(G3Ctx.out_chat_id(), send_str,
                                            parse_mode=ParseMode.HTML,
                                            disable_web_page_preview=True, timeout=TIMEOUT)

                upd_chat_last_msg(sent_msg.chat_id, sent_msg.message_id)
                return sent_msg
            except RetryAfter as retry_after:
                logger.warning(f'RetryAfter: {retry_after.retry_after}s')
                sleep(retry_after.retry_after + 1)
            except BadRequest as msg:
                if not (msg.message.startswith('Message is not modified')):
                    logger.exception(msg)
                return 'ERROR'
    else:
        sent_msg = bot.send_message(chat_id, send_str, parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True, reply_markup=reply_markup,
                                    timeout=TIMEOUT)
        upd_chat_last_msg(sent_msg.chat_id, sent_msg.message_id)
        return sent_msg


def send_audio(upd: Update, fl_s: str, caption_s: str, title=''):
    if not title:
        title = fl_s
    bot: Bot = upd.effective_message.bot
    sent_msg = bot.send_audio(upd.effective_chat.id, title=title, audio=open(fl_s, 'rb'), caption=caption_s, timeout=60)
    upd_chat_last_msg(sent_msg.chat_id, sent_msg.message_id)


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
        # reply_html(upd, reply_str)
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
