import logging
from sqlalchemy import MetaData, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Result
from sqlalchemy.engine.mock import MockConnection
from sqlalchemy.sql import Select
from sqlalchemy.sql.schema import Table

from g3b1_log.g3b1_log import cfg_logger

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def fetch_id(con: MockConnection, rs, tbl_name: str) -> int:
    if rs.rowcount != 1:
        return None
    rowid = rs.lastrowid
    if rowid:
        rs = con.execute(f"SELECT ROWID, * FROM {tbl_name} WHERE ROWID=:rowid", rowid=rowid)
        id_ = int(rs.first()['id'])
        return id_
    else:
        return None


def all_tg_user(con: MockConnection, mdata: MetaData) -> list[int]:
    tbl: Table = mdata.tables["ext_tg_user"]
    sql_sel: Select = select(tbl.columns['id'])
    rs: Result = con.execute(sql_sel)
    id_li: list[int] = []
    for row in rs:
        id_li.append(int(row.id))
    return id_li

# def iup_user_settings(con: MockConnection, meta_data: MetaData, values: dict):
#     tbl_settings: Table = meta_data.tables["user_settings"]
#     insert_stmnt: insert = insert(tbl_settings).values(values).on_conflict_do_update(
#         index_elements=['tg_user_id'],
#         set_=values
#     )
#     logger.debug(f"Insert statement: {insert_stmnt}")
#     con.execute(insert_stmnt)
#
#
# def iup_chat_user_settings(con: MockConnection, meta_data: MetaData, values: dict):
#     tbl_settings: Table = meta_data.tables["user_chat_settings"]
#     insert_stmnt: insert = insert(tbl_settings).values(values).on_conflict_do_update(
#         index_elements=['tg_user_id'],
#         set_=values
#     )
#     logger.debug(f"Insert statement: {insert_stmnt}")
#     con.execute(insert_stmnt)



# def ins_user_settings(con: MockConnection, meta_data: MetaData, values: dict):
#     tbl_settings: Table = meta_data.tables["user_settings"]
#
#     insert_stmnt: insert = insert(tbl_settings).values(values).on_conflict_do_update(
#         index_elements=['tg_user_id'],
#         set_=values
#     )
#     logger.debug(f"Insert statement: {insert_stmnt}")
#     con.execute(insert_stmnt)
