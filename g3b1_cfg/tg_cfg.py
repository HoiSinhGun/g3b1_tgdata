import ast
import codecs
import importlib
import logging
from _ast import FunctionDef
from functools import cache

from sqlalchemy import MetaData, create_engine, Table, delete, select, insert, asc
from sqlalchemy.engine import Connection, CursorResult, Row, Engine
from telegram import Update

from g3b1_data.entities import EntTy
from g3b1_data.model import G3Command, G3Module, G3Arg, script_by_file_str
from g3b1_log.log import cfg_logger

logger = cfg_logger(logging.getLogger(__name__), logging.WARN)

db_file_cfg = rf'C:\Users\IFLRGU\Documents\dev\g3b1_cfg.db'
meta_cfg = MetaData()
eng_cfg = create_engine(f"sqlite:///{db_file_cfg}")


class G3Context:
    upd: "Update" = None
    g3_m_str: str = None
    g3_cmd: "G3Command" = None
    eng: Engine = None
    md: MetaData = None


def read_functions(py_file: str):
    filename = py_file
    with codecs.open(filename, encoding='utf-8') as file:
        node = ast.parse(file.read())
    n: FunctionDef

    func_li = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name.startswith('cmd_')]

    # for function in func_li:
    #    print(function.name)
    return func_li


def init_g3_m(g3_m_file: str) -> G3Module:
    g3_m = G3Module(g3_m_file)
    cmd_dct = {}
    hdl: ast.FunctionDef
    hdl_li = read_functions(g3_m_file)
    for hdl in hdl_li:
        script = script_by_file_str(g3_m.file_main)
        cpl = compile(f"import {g3_m.name}\nfrom {g3_m.name} import {script}\n", "<string>", "exec")
        exec(cpl)
        # noinspection PyUnresolvedReferences
        g3_cmd = G3Command(g3_m, eval(f'{g3_m.name}.{script}.{hdl.name}'),
                           [G3Arg(arg.arg, G3Arg.get_annotation(arg)) for arg in hdl.args.args])
        cmd_dct.update({g3_cmd.name: g3_cmd})
        logger.debug(g3_cmd)
    g3_m.cmd_dct = cmd_dct
    ins_g3_m(g3_m)
    return g3_m


def ins_g3_m(g3_m: G3Module):
    with eng_cfg.begin() as con:
        tbl_g3_m: Table = meta_cfg.tables['g3_m']
        tbl_g3_cmd: Table = meta_cfg.tables['g3_cmd']
        tbl_g3_cmd_arg: Table = meta_cfg.tables['g3_cmd_arg']

        # noinspection PyPropertyAccess
        sel_stmnt = select(tbl_g3_m).where(tbl_g3_m.c['name'] == g3_m.name)
        rs: CursorResult = con.execute(sel_stmnt)
        if rs.fetchone():
            return

        stmnt = insert(tbl_g3_m).values(dict(name=g3_m.name, file_main=g3_m.file_main))
        con.execute(stmnt)
        rs: CursorResult = con.execute(sel_stmnt)
        g3_m_id = rs.fetchone()['id']
        for g3_cmd in g3_m.cmd_dct.values():
            stmnt = insert(tbl_g3_cmd).values(dict(g3_m_id=g3_m_id, name=g3_cmd.name,
                                                   long_name=g3_cmd.long_name, handler=g3_cmd.handler.__name__)
                                              )
            con.execute(stmnt)
            # noinspection PyPropertyAccess
            sel_stmnt = select(tbl_g3_cmd).where(tbl_g3_cmd.c.g3_m_id == g3_m_id, tbl_g3_cmd.c.name == g3_cmd.name)
            rs = con.execute(sel_stmnt)
            g3_cmd_id = rs.fetchone()['id']
            g3_arg: G3Arg
            for idx, g3_arg in enumerate(g3_cmd.g3_arg_li):
                stmnt = insert(tbl_g3_cmd_arg).values(dict(g3_cmd_id=g3_cmd_id, arg=g3_arg.arg,
                                                           annotation=g3_arg.annotation, num=idx
                                                           ))
                con.execute(stmnt)


# noinspection PyUnreachableCode
@cache
def sel_g3_m(g3_m_str: str) -> G3Module:
    ent_ty_li:list[EntTy]=[]
    if g3_m_str == 'generic':
        module_hdl = importlib.import_module(f'g3b1_serv.generic_hdl')
    else:
        module_hdl = importlib.import_module(f'{g3_m_str}.tg_hdl')
        module_mdl = importlib.import_module(f'{g3_m_str}.data.model')
        ent_ty_li = getattr(module_mdl, f'ENT_TY_{g3_m_str}_li')
    with eng_cfg.begin() as con:
        tbl_g3_m: Table = meta_cfg.tables['g3_m']
        tbl_g3_cmd: Table = meta_cfg.tables['g3_cmd']
        tbl_g3_cmd_arg: Table = meta_cfg.tables['g3_cmd_arg']
        sel_stmnt = select(tbl_g3_m).where(tbl_g3_m.c['name'] == g3_m_str)
        rs: CursorResult = con.execute(sel_stmnt)
        row = rs.fetchone()
        if not row:
            # noinspection PyTypeChecker
            return
        g3_m: G3Module = G3Module(row['file_main'], {}, id_=row['id'])
        j = tbl_g3_cmd.join(tbl_g3_cmd_arg, isouter=True)
        sel_stmnt = select(tbl_g3_cmd, tbl_g3_cmd_arg.c.arg, tbl_g3_cmd_arg.c.annotation). \
            select_from(j).where(tbl_g3_cmd.c.g3_m_id == g3_m.id_).order_by(asc(tbl_g3_cmd_arg.c.num))
        rs = con.execute(sel_stmnt)
        row_li: list[Row] = rs.fetchall()
        for row in row_li:
            cmd_name = row['name']
            if cmd_name not in g3_m.cmd_dct.keys():
                handler = getattr(module_hdl, row['handler'])
                g3_m.cmd_dct[cmd_name] = G3Command(g3_m, handler, [])
            if not row['arg']:
                continue
            g3_cmd: G3Command = g3_m.cmd_dct[cmd_name]
            g3_cmd.g3_arg_li.append(G3Arg(row['arg'], row['annotation'], ent_ty_li))
    return g3_m


def del_db_cfg():
    con: Connection
    with eng_cfg.begin() as con:
        tbl_g3_m: Table = meta_cfg.tables['g3_m']
        stmnt = delete(tbl_g3_m)
        con.execute(stmnt)


def init_db_cfg():
    con: Connection
    with eng_cfg.begin() as con:  #
        g3_m_create = 'CREATE TABLE IF NOT EXISTS "g3_m" ( ' \
                      '"id"	INTEGER NOT NULL,' \
                      '"name"	TEXT NOT NULL,' \
                      '"file_main" TEXT NOT NULL,' \
                      'UNIQUE("name"),' \
                      'PRIMARY KEY("id" AUTOINCREMENT)' \
                      ')'
        #
        g3_cmd_create = 'CREATE TABLE IF NOT EXISTS "g3_cmd" (' \
                        '"id"	INTEGER NOT NULL,' \
                        '"g3_m_id"	INTEGER NOT NULL,' \
                        '"name"	TEXT NOT NULL,' \
                        '"long_name"	TEXT NOT NULL,' \
                        '"handler"	TEXT NOT NULL,' \
                        'UNIQUE("g3_m_id", "name")' \
                        'FOREIGN KEY ("g3_m_id") REFERENCES "g3_m"("id") ON DELETE CASCADE,' \
                        'PRIMARY KEY("id" AUTOINCREMENT))'
        g3_cmd_arg_create = 'CREATE TABLE IF NOT EXISTS  "g3_cmd_arg" (' \
                            '"id"	INTEGER NOT NULL,' \
                            '"g3_cmd_id"	INTEGER NOT NULL,' \
                            '"num"	INTEGER NOT NULL,' \
                            '"arg"	TEXT NOT NULL,' \
                            '"annotation"	TEXT,' \
                            'UNIQUE("g3_cmd_id", "arg"),' \
                            'UNIQUE("g3_cmd_id", "num"),' \
                            'FOREIGN KEY ("g3_cmd_id") REFERENCES "g3_cmd"("id") ON DELETE CASCADE,' \
                            'PRIMARY KEY("id" AUTOINCREMENT))'
        #
        con.execute(g3_m_create)
        con.execute(g3_cmd_create)
        con.execute(g3_cmd_arg_create)
    meta_cfg.reflect(bind=eng_cfg)


init_db_cfg()
