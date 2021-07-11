from datetime import datetime
from queue import Queue
from typing import Union, List, Tuple

from telegram import Update, Bot, Message, User, Chat, ReplyMarkup, constants, MessageEntity
from telegram.ext import CallbackContext, Dispatcher
from telegram.utils.helpers import DEFAULT_NONE
from telegram.utils.types import ODVInput, DVInput, JSONDict

import subscribe_db
import subscribe_token


class MyMessage(Message):

    def reply_html(self, text: str, disable_web_page_preview: ODVInput[bool] = DEFAULT_NONE,
                   disable_notification: DVInput[bool] = DEFAULT_NONE, reply_to_message_id: int = None,
                   reply_markup: ReplyMarkup = None, timeout: ODVInput[float] = DEFAULT_NONE,
                   api_kwargs: JSONDict = None, allow_sending_without_reply: ODVInput[bool] = DEFAULT_NONE,
                   entities: Union[List['MessageEntity'], Tuple['MessageEntity', ...]] = None,
                   quote: bool = None) -> 'Message':
        print(text)
        return self
        # return super().reply_html(text, disable_web_page_preview, disable_notification, reply_to_message_id,
        #                          reply_markup, timeout, api_kwargs, allow_sending_without_reply, entities, quote)


def setup(module: str,
          message_id=1, chat_id=1, user_id=1, first_name='GUNNAR') \
        -> (Update, CallbackContext):
    message = MyMessage(message_id=message_id, date=datetime.now(),
                        chat=Chat(id=chat_id, type=constants.CHAT_GROUP),
                        from_user=User(id=user_id, first_name=first_name, is_bot=False)
                        )
    update = Update(1, message)
    dispatcher = Dispatcher(Bot(subscribe_db.bot_all()[module]['token']), Queue())
    ctx = CallbackContext(dispatcher)
    return update, ctx


def main():
    pass


if __name__ == '__main__':
    main()
