import logging
from typing import Optional

from sqlalchemy import MetaData, create_engine, func, select
from sqlalchemy import Table
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Result, Row, CursorResult
from sqlalchemy.engine import Connection
from sqlalchemy.event import listen
from sqlalchemy.pool import Pool
from sqlalchemy.sql import Select
from telegram import Message, Chat, User  # noqa

from g3b1_data.model import G3Result
from g3b1_data.tg_db_sqlite import tg_db_create_tables
# create console handler and set level to debug
from g3b1_log.log import cfg_logger

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


def next_negative_ext_id(chat_id: int, user_id:int) -> G3Result[int]:
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
            return G3Result(4, None)

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


def main() -> None:
    def my_on_connect(dbapi_con, connection_record):
        print("New DBAPI connection:", dbapi_con)

    listen(Pool, 'connect', my_on_connect)
    tg_db_create_tables()


if __name__ == '__main__':
    main()
