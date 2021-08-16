import logging
import sqlite3
from sqlite3 import Error

from telegram import Message, Chat, User  # noqa

DB_FILE=r'C:\Users\IFLRGU\Documents\dev\g3b1_tg.db'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


def create_conn() -> sqlite3.Connection:
    """ create a database connection to the SQLite database
            specified by db_file,
                caller responsible for closing the connection
        :return: Connection object or None
        """
    logger.debug("TODO:check_source:Creating connection")
    conn = sqlite3.connect(DB_FILE)
    return conn


def connection(conn: sqlite3.Connection):
    def cursor(func):
        """Get cursor from connection, call wrapped function"""
        logger.debug("cursor function start")

        def wrap_cursor(*args, **kwargs):
            logger.debug("wrap cursor call")
            cur = None
            try:
                logger.debug("get cursor...")
                cur = conn.cursor()
                logger.debug("and call func...")
                func(cur, *args, **kwargs)
                logger.debug("func called...")
            finally:
                if cur is not None:
                    cur.close()
                    logger.debug("Cursor closed")
                if conn is not None:
                    conn.close()
                    logger.debug("Connection closed")

        return wrap_cursor

    return cursor


# @create_connection
@connection(create_conn())
def tg_db_create_tables(cur: sqlite3.Cursor = None) -> None:
    """Init DB
    :param cur: Cursor object
    """
    logger.debug("init START")
    sql_create_user_table = """ CREATE TABLE IF NOT EXISTS tg_user (
                                    ext_id integer PRIMARY_KEY UNIQUE,
                                    is_bot integer default 0,
                                    first_name text,
                                    last_name text,
                                    username text,
                                    language_code text
                                    ) """

    sql_create_chat_table = """ CREATE TABLE IF NOT EXISTS tg_chat (
                                      ext_id integer PRIMARY_KEY UNIQUE,
                                      title text,
                                      type text,
                                      all_members_are_administrators integer default 0
                                      ) """

    sql_create_message_table = """ CREATE TABLE IF NOT EXISTS tg_message (
                                      ext_id integer PRIMARY_KEY UNIQUE,
                                      tg_user_id integer,
                                      tg_chat_id integer,
                                      date text,
                                      text text,
                                      FOREIGN KEY (tg_user_id) REFERENCES tg_user (ext_id),          
                                      FOREIGN KEY (tg_chat_id) REFERENCES tg_chat (ext_id)                            
                                      ) """

    logger.debug("Cursor for DB creation created")
    cur.execute(sql_create_user_table)
    logger.debug("DB user created")
    cur.execute(sql_create_chat_table)
    logger.debug("DB chat created")
    cur.execute(sql_create_message_table)
    logger.debug("DB message created")


def main() -> None:
    logger.debug("executing tg_db_sqlite.py main()")
    tg_db_create_tables()


if __name__ == '__main__':
    main()
