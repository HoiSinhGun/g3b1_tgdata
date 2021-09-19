import datetime
import logging
from lib2to3.patcomp import _type_of_literal

from sqlalchemy.engine import LegacyRow
from telegram import Message

from g3b1_data import tg_db
from g3b1_log.log import cfg_logger

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def main():
    row: LegacyRow = tg_db.read_latest_message(-566731880).result
    dt_object = datetime.datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S')
    message = Message(row['ext_id'], dt_object, row['tg_chat_id'],
                      row['tg_user_id'], text=row['text'])
    msg_ty = type(message)
    logger.debug(f'{msg_ty} {message.message_id} {message}')


if __name__ == '__main__':
    main()
