import logging
from dataclasses import dataclass, field
from datetime import datetime
from queue import Queue
from typing import Union, List, Tuple

from telegram import Update, Bot, Message, User, Chat, ReplyMarkup, constants, MessageEntity
from telegram.ext import CallbackContext, Dispatcher
from telegram.utils.helpers import DEFAULT_NONE
from telegram.utils.types import ODVInput, DVInput, JSONDict

import subscribe_db
import utilities
from log.g3b1_log import cfg_log_tc

logger = cfg_log_tc(__name__, logging.INFO)


class MyMessage(Message):

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
                   quote: bool = None) -> 'Message':
        logger.info(text)
        return self
        # return super().reply_html(text, disable_web_page_preview, disable_notification, reply_to_message_id,
        #                          reply_markup, timeout, api_kwargs, allow_sending_without_reply, entities, quote)


@dataclass
class TestCaseHdl:
    """TestCase for command handler function"""
    g3_cmd: utilities.G3Command
    hdl_kwargs_dct: dict[str, str]
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
                self.descr += f"{k.rjust(20, ' ')[:20]}={v.ljust(20, ' ')[:20]}"


@dataclass
class TestSuite:
    file: str
    dispatcher: Dispatcher = field(init=True, repr=False)
    tc_li: list[TestCaseHdl]
    tc_done_li: list[TestCaseHdl] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        super().__init__()
        self.tc_done_li = []

    def done_count(self) -> int:
        return len(self.tc_done_li)

    def tc_exec(self, tc: TestCaseHdl, **kwargs):
        # logger.info("".ljust(80, "="))
        logger.info(f'\n{tc.descr}')
        # logger.info("\n".ljust(80, "="))
        msg_dct = {}
        # if 'message_id' in kwargs:
        #     message_id = kwargs['message_id'] if 'message_id' in kwargs else 1
        chat: Chat = Chat(kwargs['chat_id'], constants.CHAT_GROUP) if 'chat_id' in kwargs else Chat(1,
                                                                                                    constants.CHAT_GROUP)
        first_name: str = kwargs['first_name'] if 'first_name' in kwargs else 'GUNNAR'
        user_id: int = kwargs['user_id'] if 'user_id' in kwargs else 1
        user: User = User(user_id, first_name, False)
        message_id = self.done_count() + 1
        message = MyMessage(message_id, datetime.now(),
                            chat, user)
        tc.update = Update(self.done_count() + 1, message)
        tc.ctx = CallbackContext(self.dispatcher)
        tc.g3_cmd.handler(tc.update, tc.ctx, **tc.hdl_kwargs_dct)
        self.tc_done_li.append(tc)


def setup(file: str) -> Dispatcher:
    g3_m_str = utilities.module_by_file_str(file)
    script_str = utilities.script_by_file_str(file)
    code_str = f'import {script_str}\n'
    cpl = compile(code_str, '<string>', 'exec')
    exec(cpl)
    utilities.initialize_g3_m_dct(file, eval(f'{script_str}.COLUMNS_{g3_m_str.upper()}'))
    dispatcher = Dispatcher(Bot(subscribe_db.bot_all()[g3_m_str]['token']), Queue())
    return dispatcher


def main():
    pass


if __name__ == '__main__':
    main()
