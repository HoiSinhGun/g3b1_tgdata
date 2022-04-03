"""Accessing python scripts meta data"""
import ast
import codecs
import inspect
import logging
import os
from _ast import FunctionDef, ClassDef
from enum import Enum
from functools import wraps
from typing import Any

from sqlalchemy.engine import Row, RowMapping

from constants import env_g3b1_code
from g3b1_log.log import cfg_logger

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def by_row_initializer(func):
    names, varargs, keywords, defaults, kwonlyargs, kwonlydefaults, annotations = inspect.getfullargspec(func)

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        logger.debug(f'New instance for {type(self)}')
        if 'row' in kwargs:
            row = kwargs['row']
            kwargs.pop('row')
            if isinstance(row, Row):
                # noinspection PyProtectedMember
                row_mapping: RowMapping = row._mapping
                row = row_mapping
        else:
            # noinspection PyTypeChecker
            row = {}

        if 'repl_dct' in kwargs:
            repl_dct: dict = kwargs['repl_dct']
            kwargs.pop('repl_dct')
        else:
            repl_dct = {}

        items_ = list(zip(names[1:], args)) + list(row.items()) + list(repl_dct.items())
        for name, arg in items_:
            if name == 'id':
                name = 'id_'

            if name in names:
                setattr(self, name, arg)
                kwargs[name] = arg

        for name, default in zip(reversed(names), reversed(defaults)):
            if not hasattr(self, name):
                setattr(self, name, default)
                kwargs[name] = default

        func(self, **kwargs)

    return wrapper


def ent_as_dict_sql(ent: Any, col_li: list[str] = None) -> dict[str, ]:
    val_dct = ent_as_dict(ent)
    val_dct.pop('id', '')
    val_dct.pop('id_', '')
    if not col_li:
        col_li = val_dct.keys()
    new_val_dct: dict = {}
    for col, val in {k: v for k, v in val_dct.items() if k in col_li}.items():
        # if val is None:
        #     continue
        if isinstance(val, Enum):
            new_val_dct[col] = val.value
        # check annotation for EntTy reference and add _id to its column name?
        else:
            new_val_dct[col] = val
    return new_val_dct


def ent_as_dict(ent: Any) -> dict[str,]:
    val_dct = vars(ent)
    new_val_dct = {}
    if 'id_' in val_dct:
        new_val_dct['id'] = val_dct['id_']
        val_dct.pop('id_')
    for k, v in val_dct.items():
        if hasattr(v, 'ent_ty'):
            if not k.endswith('_id'):
                k = f'{k}_id'
            if hasattr(v, 'id_'):
                new_val_dct[k] = v.id_
            else:
                new_val_dct[k] = v.id
        else:
            new_val_dct[k] = v
    return new_val_dct


def build_module_str(py_file: str) -> str:
    return os.path.normpath(
        py_file.replace(env_g3b1_code, '')[1:].replace(f'.py', '').replace(os.sep, '.')). \
        replace('g3b1_tgdata.', '')


def read_classes(py_file: str, prefix=''):
    filename = py_file
    with codecs.open(filename, encoding='utf-8') as file:
        node = ast.parse(file.read())
    n: ClassDef

    class_li = [n for n in node.body if isinstance(n, ast.ClassDef) and n.name.startswith(prefix)]

    return class_li


def read_functions(py_file: str, prefix=''):
    filename = py_file
    with codecs.open(filename, encoding='utf-8') as file:
        node = ast.parse(file.read())
    n: FunctionDef

    func_li = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name.startswith(prefix)]

    return func_li


def read_function(py_file: str, func_name: str) -> FunctionDef:
    logger.debug(str(f'Read function {func_name}'))
    with codecs.open(py_file, encoding='utf-8') as file:
        node = ast.parse(file.read())
    n: FunctionDef
    func_li = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == func_name]
    return func_li[0]
