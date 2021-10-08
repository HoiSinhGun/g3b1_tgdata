"""Accessing python scripts meta data"""
import ast
import codecs
import logging
import os
from _ast import FunctionDef, ClassDef

from constants import cfg_base_dir_code
from g3b1_log.log import cfg_logger

logger = cfg_logger(logging.getLogger(__name__), logging.WARN)


def build_module_str(py_file: str) -> str:
    return os.path.normpath(
        py_file.replace(cfg_base_dir_code, '')[1:].replace(f'.py', '').replace(os.sep, '.')). \
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
    with open(py_file) as file:
        node = ast.parse(file.read())
    n: FunctionDef
    func_li = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == func_name]
    return func_li[0]
