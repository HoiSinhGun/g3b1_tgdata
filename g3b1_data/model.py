import os
from ast import arg
from dataclasses import dataclass, field, asdict
from typing import TypeVar, Generic, Callable

T = TypeVar('T')


@dataclass
class G3Result(Generic[T]):
    retco: int = 0
    result: T = None


@dataclass
class G3Module:
    file_main: str = field(repr=False)
    cmd_dct: dict = field(default=None, repr=False)
    name: str = field(init=False)

    def __post_init__(self):
        self.name = g3m_str_by_file_str(self.file_main)


g3_m_dct: dict[str, G3Module] = {}


def script_by_file_str(file: str) -> str:
    file_name = os.path.basename(file)
    # file name without extension
    return os.path.splitext(file_name)[0]


def g3m_str_by_file_str(file: str) -> str:
    """E.g. python script base file = tg_hdl.py => subscribe.
    """
    if file.endswith('__init__.py') or file.endswith('tg_hdl.py'):
        return file.split(os.sep)[-2]
    return script_by_file_str(file).split("_")[0]


def cmd_dct_by(mod_str: str) -> dict:
    if mod_str == 'translate':
        mod_str = 'trans'
    return g3_m_dct[mod_str].cmd_dct


@dataclass
class G3Command:
    g3_m: G3Module
    handler: Callable
    args: list[arg]  # = field(init=False, repr=True)
    name: str = field(init=False, repr=True)
    long_name: str = field(init=False, repr=True)
    description: str = field(init=False, repr=True)

    def __post_init__(self):
        # Note: handler is not passed as an argument
        # here anymore, because it is not an
        # `InitVar` anymore.
        self.long_name = str(self.handler.__name__).replace('cmd_', f'{self.g3_m.name}_', 1)
        self.name = self.long_name.replace(f'{self.g3_m.name}_', '')
        self.description = self.handler.__doc__

    def as_dict_ext(self) -> dict:
        values = asdict(self)
        new_dict = dict()
        for key in values.keys():
            if values[key]:
                new_dict[key] = values[key]
        return new_dict

    def extra_args(self) -> list[arg]:
        arg_li = list[arg]()
        for item in self.args:
            if item.arg not in ['upd', 'ctx', 'reply_to_msg', 'src_msg', 'reply_to_user_id', 'chat_id', 'user_id',
                                'ent_ty']:
                arg_li.append(item)
        return arg_li

    def arg_req(self, arg_name: str) -> bool:
        for item in self.args:
            if item.arg == arg_name:
                return True
        return False

    def dotted(self) -> str:
        return self.name.replace('_', '.')

    def arg_req_ctx(self) -> bool:
        return self.arg_req('ctx')

    def arg_req_user(self) -> bool:
        return self.arg_req('user_id')

    def arg_req_ent_ty(self) -> bool:
        return self.arg_req('ent_ty')

    def arg_req_chat(self) -> bool:
        return self.arg_req('chat_id')

    def arg_req_reply_to_msg(self) -> bool:
        return self.arg_req('reply_to_msg')

    def arg_req_src_msg(self) -> bool:
        return self.arg_req('src_msg')

    def arg_req_reply_to_user_id(self) -> bool:
        return self.arg_req('reply_to_user_id')


@dataclass
class CmdExe:
    # noinspection PyUnresolvedReferences
    """Store data for command pipe execution

        Attributes:
            g3_cmd (G3Command): The command to be executed.
            input (:list:`str`): Input to the command execution.
            g3_cmd_li (:list:`G3Command`): The next commands in the pipe
            res_cmd_exe_li (:list:`CmdExe`): The output (single or many rows) of the execution is the input for the next
                command to be execute.
        """
    g3_cmd: G3Command
    input: list[str]
    g3_cmd_li: list[G3Command]
    res_cmd_li: list["CmdExe"] = field(init=False, repr=False, compare=False)
