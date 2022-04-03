import _ast
import os
from dataclasses import dataclass, field, asdict
from typing import TypeVar, Generic, Callable, Optional, Union

from constants import env_g3b1_code
from g3b1_data.elements import EleTy, EleVal
from g3b1_data.entities import EntTy

T = TypeVar('T')


def script_by_file_str(file: str) -> str:
    file_name = os.path.basename(file)
    # file name without extension
    return os.path.splitext(file_name)[0]


def g3m_str_by_file_str(file: str) -> str:
    """E.g. python script base file = trans__tg_hdl.py => subscribe.
    New file pattern: {g3_m_str}__tg_hdl.py, e.g. trans__tg_hdl.py
    """
    if file.endswith('__init__.py') or file.endswith('trans__tg_hdl.py'):
        return file.split(os.sep)[-2]
    if script_by_file_str(file).split("_")[0] == 'generic':
        return 'generic'
    else:
        return file.replace(env_g3b1_code, '')


class G3Result(Generic[T]):

    def __init__(self, retco: int = 0, result: T = None) -> None:
        super().__init__()
        self.retco: int = retco
        self.result: T = result

    @classmethod
    def from_ele_val(cls, ele_val: EleVal) -> "G3Result":
        if ele_val.val:
            return cls(result=ele_val.val)
        else:
            return cls(4)


@dataclass
class G3Module:
    file_main: str = field(repr=False)
    cmd_dct: dict[str, Union["G3Func", "G3Command"]] = field(default=None, repr=False)
    name: str = field(init=False)
    id_: int = None

    def __post_init__(self):
        self.name = g3m_str_by_file_str(self.file_main)

    def add_g3_func(self, g3_func):
        if not self.cmd_dct:
            self.cmd_dct = {}
        self.cmd_dct.update({g3_func.name, g3_func})


@dataclass
class G3Command:
    g3_m: G3Module
    handler: Callable
    g3_arg_li: list["G3Arg"]  # = field(init=False, repr=True)
    icon: str = field(init=False, repr=True)
    name: str = field(init=False, repr=True)
    long_name: str = field(init=False, repr=True)
    description: str = field(init=False, repr=True)
    id_: int = None
    special_arg_li = ['upd', 'ctx', 'reply_to_msg', 'src_msg', 'src_bot_msg', 'reply_to_user_id', 'chat_id', 'user_id',
                      'ent_ty']

    def __post_init__(self):
        self.long_name = str(self.handler.__name__).replace('cmd_', f'{self.g3_m.name}_', 1)
        self.name = self.long_name.replace(f'{self.g3_m.name}_', '')
        self.description = self.handler.__doc__
        self.icon = ''
        if self.description and len(self.description) > 1 and self.description[1] == ' ':
            self.icon = self.description[0]

    def as_dict_ext(self) -> dict:
        values = asdict(self)
        new_dict = dict()
        for key in values.keys():
            if values[key]:
                new_dict[key] = values[key]
        return new_dict

    def extra_args(self) -> list["G3Arg"]:
        arg_li = list["G3Arg"]()
        for item in self.g3_arg_li:
            # if item.annotation not in ['str', 'int']:
            #     continue
            if item.arg not in self.special_arg_li:
                arg_li.append(item)
        return arg_li

    def ent_ty_args(self) -> list["G3Arg"]:
        return [arg for arg in self.g3_arg_li if arg.ent_ty is not None]

    def has_arg(self, arg_name: str) -> bool:
        for item in self.g3_arg_li:
            if item.arg == arg_name:
                return True
        return False

    def dotted(self) -> str:
        return self.name.replace('_', '.')

    def has_arg_upd(self) -> bool:
        return self.has_arg('upd')

    def has_arg_ctx(self) -> bool:
        return self.has_arg('ctx')

    def has_arg_user(self) -> bool:
        return self.has_arg('user_id')

    def has_arg_ent_ty(self) -> bool:
        return self.has_arg('ent_ty')

    def has_arg_chat(self) -> bool:
        return self.has_arg('chat_id')

    def has_arg_reply_to_msg(self) -> bool:
        return self.has_arg('reply_to_msg')

    def has_arg_src_msg(self) -> bool:
        return self.has_arg('src_msg')

    def has_arg_src_bot_msg(self) -> bool:
        return self.has_arg('src_bot_msg')

    def has_arg_reply_to_user_id(self) -> bool:
        return self.has_arg('reply_to_user_id')

    def is_ins_ent(self):
        return self.name.endswith('_01')

    def is_pick_ent(self):
        return self.name.endswith('_04')


class G3Arg:

    def __init__(self, arg_: str, annotation: str, ent_ty_li: list[EntTy] = None,
                 ele_ty_li: list[EleTy] = None) -> None:
        super().__init__()
        self.arg = arg_
        self.annotation = annotation
        self.f_required = self.arg.startswith('req__')
        self.f_current = self.arg.startswith('cur__')
        # noinspection PyTypeChecker
        self.ent_ty: EntTy = None
        # noinspection PyTypeChecker
        self.ele_ty: EleTy = None
        if not ent_ty_li:
            return
        for ent_ty in [i for i in ent_ty_li if i.type == annotation]:
            self.ent_ty = ent_ty
        ele_id = self.arg
        if self.f_current or self.f_required:
            ele_id = ele_id[5:]
        ele_id += '_id'
        self.ele_ty = EleTy.by_ent_ty(self.ent_ty, ele_ty_li)

    @staticmethod
    def get_annotation(arg: _ast.arg) -> str:
        if arg.annotation:
            # noinspection PyUnresolvedReferences
            return arg.annotation.id
        else:
            return ''


class G3Func:

    def __init__(self, g3_m: G3Module, func: Callable, fname: str, g3_arg_li: list[G3Arg]) -> None:
        super().__init__()
        self.g3_m: G3Module = g3_m
        self.func = func
        self.name = fname
        self.g3_arg_li: list[G3Arg] = g3_arg_li
        g3_m.add_g3_func(self)


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


class Menu:

    def __init__(self, id_: str, lbl: str) -> None:
        super().__init__()
        self.id = id_
        self.lbl = lbl
        self.it_li: list["MenuIt"] = []

    @classmethod
    def for_g3m(cls, g3m: G3Module) -> "Menu":
        return cls(g3m.name, g3m.name)

    def first_level(self) -> list["MenuIt"]:
        return [mi for mi in self.it_li if mi.parent is None]

    def mi_by_id(self, id_: str) -> "MenuIt":
        mi_li: list[MenuIt] = [mi for mi in self.it_li if mi.id == id_]
        if not mi_li:
            # noinspection PyTypeChecker
            return
        return mi_li[0]


class MenuIt:

    def __init__(self, id_: str = '', lbl: str = '', parent: "MenuIt" = None, g3_cmd: Optional[G3Command] = None,
                 menu: Optional[Menu] = None, args_str='') -> None:
        super().__init__()
        self.menu = menu
        if not self.menu and parent:
            self.menu = parent.menu
        self.parent = parent
        if self.parent and id_:
            self.id = f'{self.parent.id}:{id_}'
        elif g3_cmd and self.menu:
            self.id = g3_cmd.name
        else:
            self.id = id_
        if lbl:
            self.lbl = lbl
        else:
            self.lbl = self.id
        self.g3_cmd: G3Command = g3_cmd
        self.it_li = []
        if self.menu:
            self.menu.it_li.append(self)
        self.args_str = args_str
        if self.parent:
            self.parent.it_li.append(self)

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __hash__(self) -> int:
        return hash(self.id)

    def lbl_w_icon(self) -> str:
        if self.it_li:
            i = '📂'
        elif self.id.endswith('_01'):
            i = '📝'
        elif self.id.endswith('_03'):
            i = '🔎'
        elif self.id.endswith('_04'):
            i = '👉'
        elif self.id.endswith('_33'):
            i = '🔍'
        elif self.id.endswith('back'):
            i = '👈'
        else:
            return self.lbl
        return f'{i} {self.lbl}'
