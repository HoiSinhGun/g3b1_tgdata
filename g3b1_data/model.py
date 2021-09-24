import _ast
import os
from dataclasses import dataclass, field, asdict
from typing import TypeVar, Generic, Callable, Optional

from g3b1_data.elements import EleTy
from g3b1_data.entities import EntTy
from g3b1_serv.str_utils import uncapitalize

T = TypeVar('T')


@dataclass
class G3Result(Generic[T]):
    retco: int = 0
    result: T = None


@dataclass
class G3Module:
    file_main: str = field(repr=False)
    cmd_dct: dict[str, "G3Command"] = field(default=None, repr=False)
    name: str = field(init=False)
    id_: int = None

    def __post_init__(self):
        self.name = g3m_str_by_file_str(self.file_main)


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


@dataclass
class G3Command:
    g3_m: G3Module
    handler: Callable
    g3_arg_li: list["G3Arg"]  # = field(init=False, repr=True)
    name: str = field(init=False, repr=True)
    long_name: str = field(init=False, repr=True)
    description: str = field(init=False, repr=True)
    id_: int = None
    special_arg_li = ['upd', 'ctx', 'reply_to_msg', 'src_msg', 'reply_to_user_id', 'chat_id', 'user_id',
                      'ent_ty']

    def __post_init__(self):
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

    def arg_req(self, arg_name: str) -> bool:
        for item in self.g3_arg_li:
            if item.arg == arg_name:
                return True
        return False

    def dotted(self) -> str:
        return self.name.replace('_', '.')

    def arg_req_upd(self) -> bool:
        return self.arg_req('upd')

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

    def is_ins_ent(self):
        return self.name.endswith('_01')

    def is_pick_ent(self):
        return self.name.endswith('_04')

class G3Arg:

    def __init__(self, arg_: str, annotation: str, ent_ty_li: list[EntTy] = None) -> None:
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
        for ent_ty in [i for i in ent_ty_li if i.id == uncapitalize(annotation)]:
            self.ent_ty = ent_ty
            self.ele_ty = EleTy.by_ent_ty(ent_ty)

    @staticmethod
    def get_annotation(arg: _ast.arg) -> str:
        if arg.annotation:
            # noinspection PyUnresolvedReferences
            return arg.annotation.id
        else:
            return ''


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
                 menu: Optional[Menu] = None) -> None:
        super().__init__()
        if menu:
            self.menu = menu
        else:
            self.menu = parent.menu
        self.parent = parent
        if self.parent and id_:
            self.id = f'{self.parent.id}:{id_}'
        elif g3_cmd:
            self.id = g3_cmd.name
        else:
            self.id = id_
        if lbl:
            self.lbl = lbl
        else:
            self.lbl = self.id
        self.g3_cmd: G3Command = g3_cmd
        self.it_li = []
        self.menu.it_li.append(self)
        if self.parent:
            self.parent.it_li.append(self)

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __hash__(self) -> int:
        return hash(self.id)
