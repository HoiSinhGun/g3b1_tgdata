import logging

from sqlalchemy import Table
from sqlalchemy import MetaData, create_engine
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine.mock import MockConnection
from telegram import Message, Chat, User  # noqa
from tg_db_sqlite import tg_db_create_tables

# create console handler and set level to debug
from log.g3b1_log import cfg_logger

DB_FILE_TG = r'C:\Users\IFLRGU\Documents\dev\g3b1_tg.db'
MetaData_TG = MetaData()
Engine_TG = create_engine(f"sqlite:///{DB_FILE_TG}")
MetaData_TG.reflect(bind=Engine_TG)

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)

TABLE_TG_USER = "tg_user"
TABLE_TG_CHAT = "tg_chat"


def synchronize_user(con: MockConnection, row: User):
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


def synchronize_chat(con: MockConnection, row: Chat):
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


def synchronize_message(con: MockConnection, row: Message):
    tg_table: Table = MetaData_TG.tables["tg_message"]
    logger.debug(f"Table: {tg_table}")
    logger.debug(f"Row: {row}")
    values = dict(ext_id=row.message_id, tg_user_id=row.from_user.id, tg_chat_id=row.chat.id,
                  date=row.date.strftime('%Y-%m-%d %H:%M:%S'), text=row.text
                  )
    tg_insert: insert = insert(tg_table).values(values).on_conflict_do_update(
        index_elements=['tg_chat_id', 'ext_id'],
        set_=values
    )
    logger.debug(f"Insert statement: {tg_insert}")
    con.execute(tg_insert)
    Engine_TG.execute(tg_insert)


def synchronize_from_message(message: Message) -> None:
    """ Doc
    """

    with Engine_TG.connect() as con:
        synchronize_user(con, message.from_user)
        synchronize_chat(con, message.chat)
        synchronize_message(con, message)


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


def main() -> None:
    tg_db_create_tables()


if __name__ == '__main__':
    main()
