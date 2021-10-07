import logging
from dataclasses import asdict
from enum import Enum
from typing import Optional, Any, Dict

from sqlalchemy import MetaData, create_engine, func, select, and_
from sqlalchemy import Table
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Connection
from sqlalchemy.engine import Result, Row, CursorResult
from sqlalchemy.event import listen
from sqlalchemy.pool import Pool
from sqlalchemy.sql import Select
from telegram import Message, Chat, User  # noqa

from elements import ELE_TY_chat_id
from entities import EntId, ET, EntTy, get_meta_attr
from g3b1_cfg.tg_cfg import G3Ctx
from g3b1_data.integrity import orm
from g3b1_data.model import G3Result
from g3b1_data.tg_db_sqlite import tg_db_create_tables
# create console handler and set level to debug
from g3b1_log.log import cfg_logger
from generic_mdl import ele_ty_by_ent_ty

DB_FILE_TG = r'C:\Users\IFLRGU\Documents\dev\g3b1_tg.db'
MetaData_TG = MetaData()
Engine_TG = create_engine(f"sqlite:///{DB_FILE_TG}")
MetaData_TG.reflect(bind=Engine_TG)

logger = cfg_logger(logging.getLogger(__name__), logging.WARN)

TABLE_TG_USER = "tg_user"
TABLE_TG_CHAT = "tg_chat"


def fetch_id(con: Connection, rs, tbl_name: str) -> Optional[int]:
    if rs.rowcount != 1:
        return None
    rowid = rs.lastrowid
    if rowid:
        rs: CursorResult = con.execute(f"SELECT ROWID, * FROM {tbl_name} WHERE ROWID=:rowid", rowid=rowid)
        id_ = int(rs.first()['id'])
        return id_
    else:
        return None


def next_negative_ext_id(chat_id: int, user_id: int) -> G3Result[int]:
    with Engine_TG.connect() as con:
        tg_table: Table = MetaData_TG.tables["tg_message"]
        cols = tg_table.columns
        sql_sel: Select = select(func.min(cols['ext_id']).label('ext_id'))
        where_clause = ((cols.tg_chat_id == chat_id) & (cols.tg_user_id == user_id))
        sql_sel = sql_sel.where(where_clause)

        logger.debug(sql_sel)
        rs: Result = con.execute(sql_sel)
        result = rs.first()

        if not result:
            return G3Result(0, -1)

        ext_id = result['ext_id'] - 1
        if ext_id >= 0:
            ext_id = -1
        return G3Result(0, ext_id)


def read_latest_message(chat_id: int, user_id: int, is_cmd_explicit=False, g3m_str='') -> G3Result[Row]:
    with Engine_TG.connect() as con:
        tg_table: Table = MetaData_TG.tables["tg_message"]
        cols = tg_table.columns
        sql_sel: Select = select(cols['tg_chat_id'], cols['ext_id'], cols['tg_user_id'],
                                 func.max(cols['date']).label('date'), cols['text'])
        where_clause = ((cols.tg_chat_id == chat_id) & (cols.tg_user_id == user_id) & (
                cols.g3_cmd_explicit == is_cmd_explicit))
        if g3m_str:
            where_clause = (where_clause & (cols.bot_module == g3m_str))
        sql_sel = sql_sel.where(where_clause)

        logger.debug(sql_sel)
        rs: Result = con.execute(sql_sel)
        result = rs.first()

        if not result:
            return G3Result(4)

        return G3Result(0, result)


def synchronize_user(con: Connection, row: User):
    tg_table: Table = MetaData_TG.tables["tg_user"]
    logger.debug(f"Table: {tg_table}")
    logger.debug(f"Row: {row}")
    values = dict(ext_id=row.id, username=row.username, first_name=row.first_name,
                  last_name=row.last_name, language_code=row.language_code,
                  is_bot=int(row.is_bot))
    tg_insert: insert = insert(tg_table).values(values).on_conflict_do_update(
        index_elements=['ext_id'],
        set_=values
    )
    logger.debug(f"Insert statement: {tg_insert}")
    con.execute(tg_insert)


def synchronize_chat(con: Connection, row: Chat):
    tg_table: Table = MetaData_TG.tables["tg_chat"]
    logger.debug(f"Table: {tg_table}")
    logger.debug(f"Row: {row}")
    values = dict(ext_id=row.id, title=row.title, all_members_are_administrators=row.all_members_are_administrators)
    tg_insert: insert = insert(tg_table).values(values).on_conflict_do_update(
        index_elements=['ext_id'],
        set_=values
    )
    logger.debug(f"Insert statement: {tg_insert}")
    con.execute(tg_insert)


def synchronize_message(con: Connection,
                        row: Message,
                        g3_cmd_long_str: str = None, is_command_explicit: bool = None):
    tg_table: Table = MetaData_TG.tables["tg_message"]
    logger.debug(f"Table: {tg_table}")
    logger.debug(f"Row: {row}")
    bot_module: str = row.bot.username.split('_')[1]
    if bot_module == 'translate':
        bot_module = 'trans'
    values = dict(ext_id=row.message_id, tg_user_id=row.from_user.id, tg_chat_id=row.chat.id,
                  date=row.date.strftime('%Y-%m-%d %H:%M:%S'), text=row.text,
                  bot_module=bot_module,
                  g3_cmd=g3_cmd_long_str, g3_cmd_explicit=is_command_explicit
                  )
    tg_insert: insert = insert(tg_table).values(values).on_conflict_do_update(
        index_elements=['tg_chat_id', 'ext_id'],
        set_=values
    )
    logger.debug(f"Insert statement: {tg_insert}")
    con.execute(tg_insert)
    Engine_TG.execute(tg_insert)


def synchronize_from_message(
        message: Message, g3_cmd_long_str: str = None, is_command_explicit: bool = None) \
        -> None:
    """ Doc
    """
    with Engine_TG.connect() as con:
        if not message.from_user:
            logger.error(f'message.from_user empty?')
        else:
            synchronize_user(con, message.from_user)
        synchronize_chat(con, message.chat)
        synchronize_message(con, message, g3_cmd_long_str, is_command_explicit)


def externalize_user_id(bot_bkey: str, id_: int) -> None:
    externalize_id(bot_bkey, TABLE_TG_USER, id_)


def externalize_chat_id(bot_bkey: str, id_: int) -> None:
    externalize_id(bot_bkey, TABLE_TG_CHAT, id_)


def externalize_id(bot_bkey: str, tg_tbl_name: str, id_: int) -> None:
    """
    Writes simply the id in the DB of the related satellite app.
    There is no validation of the id.
    """
    tbl_name = f'ext_{tg_tbl_name}'
    ext_db_file = rf'C:\Users\IFLRGU\Documents\dev\g3b1_{bot_bkey}.db'
    ext_meta_data = MetaData()
    ext_engine = create_engine(f"sqlite:///{ext_db_file}")
    ext_meta_data.reflect(bind=ext_engine)
    with ext_engine.connect() as con:
        ext_table: Table = ext_meta_data.tables[tbl_name]
        logger.debug(f"Table: {ext_table}")
        values = dict(id=id_)
        ext_insert: insert = insert(ext_table).values(values).on_conflict_do_update(
            index_elements=['id'],
            set_=values
        )
        logger.debug(f"Insert statement: {ext_insert}")
        con.execute(ext_insert)


def sel_msg_rng_by_chat_user(from_msg_id, chat_id, user_id) -> G3Result[list[dict]]:
    with Engine_TG.connect() as con:
        tg_table: Table = MetaData_TG.tables["tg_message"]
        cols = tg_table.columns
        sql_sel: Select = select(cols['tg_chat_id'], cols['ext_id'], cols['tg_user_id'],
                                 cols['date'], cols['text'])
        sql_sel = sql_sel.where(cols.tg_chat_id == chat_id, cols.tg_user_id == user_id,
                                cols.ext_id >= from_msg_id,
                                cols.g3_cmd_explicit == False)
        logger.debug(sql_sel)
        rs: Result = con.execute(sql_sel)
        rs = rs.fetchall()
        msg_dct_li = []
        for row in rs:
            d = dict(row)
            msg_dct_li.append(d)

        return G3Result(0, msg_dct_li)


def sel_ent_ty(ent_id: EntId[ET], con: Connection = None) -> G3Result[ET]:
    ent_ty = ent_id.ent_ty
    from_row_any, md, eng = get_meta_attr(ent_ty)

    # noinspection PyShadowingNames
    def wrapped(con: Connection):
        tbl: Table = md.tables[ent_ty.tbl_name]
        c = tbl.columns
        if isinstance(ent_id.id, int):
            where = (c['id'] == ent_id.id)
        else:
            bkey_clause = (c['bkey'] == ent_id.id)
            if ent_id.g3_bot_id:
                where = and_(
                    c['g3_bot_id'] == ent_id.g3_bot_id,
                    bkey_clause
                )
            elif ELE_TY_chat_id.id_ in tbl.c:
                where = and_(
                    c[ELE_TY_chat_id.id_] == G3Ctx.chat_id(),
                    bkey_clause
                )
            else:
                where = bkey_clause

        stmnt = (select(tbl).
                 where(where))

        rs: Result = con.execute(stmnt)
        row: Row = rs.first()
        # fetch fk entities:
        repl_dct = orm(con, tbl, row, from_row_any, {})
        ent: ET = from_row_any(ent_ty, row, repl_dct)
        for k, v in ent_ty.it_ent_ty_dct.items():
            it_li = sel_ent_ty_by_par(ent, v, con)
            setattr(ent, k, it_li)

        return G3Result(0, ent)

    if not con:
        with eng.connect() as con:
            return wrapped(con)
    else:
        return wrapped(con)


def sel_ent_ty_by_par(ent: Any, ent_ty: ET, con: Connection = None) -> list[Any]:
    from_row_any, md, eng = get_meta_attr(ent_ty)
    ent_ty_par: EntTy = ent.ent_ty
    ele_ty_par = ele_ty_by_ent_ty(ent_ty_par)
    id_attr = getattr(ent, 'id')
    if not id_attr:
        id_attr = getattr(ent, 'id_')
    repl_dct = {ele_ty_par.col_name: ent}

    # noinspection PyShadowingNames
    def wrapped(con: Connection, repl_dct: dict) -> list[Any]:
        tbl: Table = md.tables[ent_ty.tbl_name]
        c = tbl.columns
        stmnt = (select(tbl).
                 where(c[ele_ty_par.col_name] == id_attr))
        cr: CursorResult = con.execute(stmnt)
        row_li: list[Row] = cr.fetchall()
        res_li: list[Any] = []
        for row in row_li:
            repl_dct = orm(con, tbl, row, from_row_any, repl_dct)
            ent: ET = from_row_any(ent_ty, row, repl_dct)
            for k, v in ent_ty.it_ent_ty_dct.items():
                it_li = sel_ent_ty_by_par(ent, v, con)
                setattr(ent, k, it_li)
            res_li.append(ent)
        return res_li

    if not con:
        with eng.connect() as con:
            return wrapped(con, repl_dct)
    else:
        return wrapped(con, repl_dct)


def sel_ent_ty_li(ent_ty: EntTy) -> list[Row]:
    tbl: Table = G3Ctx.md.tables[ent_ty.tbl_name]
    chat_id = G3Ctx.chat_id()
    c = tbl.columns
    with G3Ctx.eng.begin() as con:
        if 'chat_id' in c:
            stmnt = (select(tbl).
                     where(c['chat_id'] == chat_id))
        else:
            stmnt = (select(tbl))
        rs: CursorResult = con.execute(stmnt)
        return rs.fetchall()


def ins_ent_ty(ent: Any) -> G3Result[Any]:
    val_dct = asdict(ent)
    new_val_dct: dict = {}
    for k, v in val_dct.items():
        if v is None:
            continue
        if isinstance(v, Enum):
            new_val_dct[k] = v.value
        elif isinstance(v, Dict):
            new_val_dct[f'{k}_id'] = v['id_']
        else:
            new_val_dct[k] = v
    with G3Ctx.eng.begin() as con:
        tbl: Table = G3Ctx.md.tables[ent.ent_ty().tbl_name]
        stmnt = (insert(tbl).
                 values(new_val_dct))
        rs: CursorResult = con.execute(stmnt)
        if not (id_ := fetch_id(con, rs, tbl.name)):
            return G3Result(4)
        g3r = sel_ent_ty(EntId(ent.ent_ty(), id_), con)
        return g3r


def main() -> None:
    def my_on_connect(dbapi_con, connection_record):
        print("New DBAPI connection:", dbapi_con)

    listen(Pool, 'connect', my_on_connect)
    tg_db_create_tables()


if __name__ == '__main__':
    main()
