import logging
from dataclasses import dataclass, field
from datetime import datetime
from queue import Queue
from typing import Union, List, Tuple

from sqlalchemy import MetaData
from sqlalchemy.engine import Engine
from telegram import Update, Bot, Message, User, Chat, ReplyMarkup, constants, MessageEntity
from telegram.ext import CallbackContext, Dispatcher
from telegram.utils.helpers import DEFAULT_NONE
from telegram.utils.types import ODVInput, DVInput, JSONDict

from g3b1_cfg.tg_cfg import init_g3_m, G3Ctx
from g3b1_log.log import cfg_log_tc
from g3b1_serv import utilities
from subscribe.data import db

logger = cfg_log_tc(__name__, logging.INFO)


class MockChat:

    def __init__(self, id_: int) -> None:
        super().__init__()
        self.id = id_


class MockUser:

    def __init__(self, id_: int) -> None:
        super().__init__()
        self.id = id_


class MockUpdate:

    @classmethod
    def sample(cls) -> "MockUpdate":
        return cls(MockChat(-1), MockUser(1))

    def __init__(self, chat: MockChat, user: MockUser) -> None:
        super().__init__()
        self.effective_chat = chat
        self.effective_user = user


class MsgCallback(object):
    msg_li: list[str] = []

    def add_msg(self, msg_str: str):
        self.msg_li.append(msg_str)


class MyMessage(Message):
    msg_callback: MsgCallback

    @staticmethod
    def from_data_dict(data_dct: dict):
        # msg_dct: dict
        # msg_dct.update({'message_id': data_dct['message_id']})
        # for k, v in data_dct.items():
        #
        # message_id = kwargs['message_id'], date = datetime.now(),
        # chat = Chat(id=kwargs['chat_id'], type=constants.CHAT_GROUP),
        # from_user = User(id=kwargs['user_id'], first_name=kwargs['first_name'], is_bot=False)
        #
        # MyMessage()
        pass

    def reply_html(self, text: str, disable_web_page_preview: ODVInput[bool] = DEFAULT_NONE,
                   disable_notification: DVInput[bool] = DEFAULT_NONE, reply_to_message_id: int = None,
                   reply_markup: ReplyMarkup = None, timeout: ODVInput[float] = DEFAULT_NONE,
                   api_kwargs: JSONDict = None, allow_sending_without_reply: ODVInput[bool] = DEFAULT_NONE,
                   entities: Union[List['MessageEntity'], Tuple['MessageEntity', ...]] = None,
                   quote: bool = None, chat_id=None, parse_mode=None) -> 'Message':
        if MyMessage.msg_callback:
            if isinstance(text, int):
                # Guess why :-)
                MyMessage.msg_callback.add_msg(str(disable_web_page_preview))
            else:
                MyMessage.msg_callback.add_msg(text)
            if reply_markup:
                # noinspection PyTypeChecker
                keyboard: list[list[dict[str, str]]] = reply_markup['keyboard']
                for row in keyboard:
                    # print(' '.join([i['text'] for i in row]))
                    for text in [i['text'] for i in row]:
                        print(text)
                for idx_row, row in enumerate(keyboard):
                    print(' '.join([f'{idx_row}{idx}{i["text"]}' for idx, i in enumerate(row)]))

        else:
            logger.info(text)
        return self
        # return super().reply_html(text, disable_web_page_preview, disable_notification, reply_to_message_id,
        #                          reply_markup, timeout, api_kwargs, allow_sending_without_reply, entities, quote)


def g3_context_mock(eng: Engine, md: MetaData, g3_m_str='MOCK'):
    G3Ctx.upd = MockUpdate.sample()
    G3Ctx.g3_m_str = g3_m_str
    G3Ctx.eng = eng
    G3Ctx.md = md


def user_default() -> User:
    return User(1, "Gunnar", False)


def chat_default() -> Chat:
    return Chat(1, constants.CHAT_GROUP)


@dataclass
class TestCaseHdl:
    """TestCase for command handler function"""
    g3_cmd: utilities.G3Command
    hdl_kwargs_dct: dict[str, ...]
    # the kwargs value will be = utilities.G3Command.hdl(args, kwargs)
    # all parameters passed to tc_exec(tc: TestCaseHdl
    setup_cmd_li: list[utilities.G3Command] = None
    descr: str = field(init=False)
    upd: Update = field(init=False, repr=False)
    ctx: CallbackContext = field(init=False, repr=False)

    def __post_init__(self):
        self.descr = f'=> Exec {self.g3_cmd.name.ljust(20, " ")[:20]} with:\n'
        if len(self.hdl_kwargs_dct) == 0:
            self.descr += 'No arguments'
        else:
            for k, v in self.hdl_kwargs_dct.items():
                self.descr += f"{k.rjust(15, ' ')[:15]} = {str(v).ljust(20, ' ')[:20]}\n"


@dataclass
class TestSuite:
    dispatcher: Dispatcher = field(init=True, repr=False)
    tc_li: list[TestCaseHdl]
    tc_done_li: list[TestCaseHdl] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        super().__init__()
        self.tc_done_li = []

    def done_count(self) -> int:
        return len(self.tc_done_li)

    def tc_exec(self, tc: TestCaseHdl, msg_callback: MsgCallback = None):
        kwargs = tc.hdl_kwargs_dct
        # logger.info("".ljust(80, "="))
        logger.info(f'\n{tc.descr}')
        # logger.info("\n".ljust(80, "="))
        msg_dct = {}
        # if 'message_id' in kwargs:
        #     message_id = kwargs['message_id'] if 'message_id' in kwargs else 1
        chat: Chat
        if 'chat_id' in kwargs.keys():
            chat = Chat(int(kwargs['chat_id']), constants.CHAT_GROUP)
            kwargs.pop('chat_id')
        else:
            chat = Chat(1, constants.CHAT_GROUP)

        if 'first_name' in kwargs:
            first_name: str = kwargs['first_name']
            kwargs.pop('first_name')
        else:
            first_name = 'GUNNAR'

        if 'user_id' in kwargs:
            user_id: int = int(kwargs['user_id'])
            kwargs.pop('user_id')
        else:
            user_id = 1

        if 'reply_to_msg' in kwargs:
            reply_to_msg: Message = kwargs['reply_to_msg']
            kwargs.pop('reply_to_msg')
        else:
            # noinspection PyTypeChecker
            reply_to_msg = None

        user: User = User(user_id, first_name, False)
        message_id = self.done_count() + 1
        message = MyMessage(message_id, datetime.now(),
                            chat=chat, from_user=user, reply_to_message=reply_to_msg)
        MyMessage.msg_callback = msg_callback
        tc.update = Update(self.done_count() + 1, message)
        tc.ctx = CallbackContext(self.dispatcher)
        args = (tc.update, tc.ctx)
        tc.g3_cmd.handler(*args, **kwargs)
        self.tc_done_li.append(tc)


def upd_builder(message_id: int = -333, chat=Chat(1, constants.CHAT_GROUP),
                user=User(1, 'Gunnar', False), reply_to_msg=None) -> Update:
    message = MyMessage(message_id, datetime.now(),
                        chat=chat, from_user=user, reply_to_message=reply_to_msg)
    return Update(-333, message)


def setup(file: str) -> Dispatcher:
    g3_m = init_g3_m(file)
    bot_row = db.bot_all()[g3_m.name]
    bot = Bot(bot_row['token'])
    bot._bot = User(-666, 'bot', True, username=f'g3b1_{bot_row["bkey"]}')
    dispatcher = Dispatcher(bot, Queue())
    return dispatcher


def main():
    pass


if __name__ == '__main__':
    main()
