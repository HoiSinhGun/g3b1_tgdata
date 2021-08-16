import logging

from sqlalchemy import MetaData, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Result
from sqlalchemy.engine.mock import MockConnection
from sqlalchemy.sql import Select
from sqlalchemy.sql.schema import Table

from g3b1_data.model import G3Result
from g3b1_log.g3b1_log import cfg_logger

logger = cfg_logger(logging.getLogger(__name__), logging.WARN)


def chat_setting(
        chat_id: int, ele: dict[str, str], ele_val: str = None) -> dict[str, ...]:
    """Prepare arg dictionary for a setting for the chat_id
    to read or write"""
    params = dict(chat_id=chat_id, colname=ele['colname'], ele_id=ele)
    if ele_val is not None:
        params['ele_val'] = ele_val
    return params


def user_setting(
        user_id: int, ele: dict[str, str], ele_val: str = None) -> dict[str, ...]:
    """Prepare arg dictionary for a setting for the user_id
    to read or write"""
    params = dict(user_id=user_id, colname=ele['colname'])
    if ele_val is not None:
        params['ele_val'] = ele_val
    return params


def chat_user_setting(chat_id: int, user_id: int, ele_id: dict, ele_val: str = None) -> dict[str, ]:
    """Prepare arg dictionary for a setting for the chat_id/user_id
        to read or write"""
    params = dict(chat_id=chat_id, user_id=user_id, ele_id=ele_id)
    if ele_val is not None:
        params['ele_val'] = ele_val
    return params


def iup_setting(con: MockConnection, meta_data: MetaData, params: dict[str, ...]) -> G3Result:
    is_chat, is_user, tbl_name, tg_chat_id, tg_user_id = chat_user_setng_params(params)
    values: dict = {}
    index_elements: list = []
    if is_user:
        values = dict(tg_user_id=tg_user_id)
        index_elements.append('tg_user_id')
    if is_chat:
        values['tg_chat_id'] = tg_chat_id
        index_elements.append('tg_chat_id')
    if 'ele_id' in params.keys():
        ele_id = params['ele_id']['colname']
        if params['ele_val'] == 'None':
            values[ele_id] = None
        else:
            values[ele_id] = params['ele_val']
    tbl_settings: Table = meta_data.tables[tbl_name]

    insert_stmnt: insert = insert(tbl_settings).values(values).on_conflict_do_update(
        index_elements=index_elements,
        set_=values
    )
    logger.debug(f"InsUpd statement: {insert_stmnt}")
    con.execute(insert_stmnt)
    return G3Result()


def read_setting(con: MockConnection, meta_data: MetaData, params: dict[str, ...]) -> G3Result:
    is_chat, is_user, tbl_name, tg_chat_id, tg_user_id = chat_user_setng_params(params)

    tbl_settings: Table = meta_data.tables[tbl_name]
    tbl_cols = tbl_settings.columns
    colname = params['ele_id']['colname']
    sql_sel: Select = select(tbl_settings.columns[colname])

    if is_chat and is_user:
        sql_sel = sql_sel.where(tbl_cols.tg_chat_id == tg_chat_id, tbl_cols.tg_user_id == tg_user_id)
    elif is_user:
        sql_sel = sql_sel.where(tbl_cols.tg_user_id == tg_user_id)
    elif is_chat:
        sql_sel = sql_sel.where(tbl_cols.tg_chat_id == tg_chat_id)

    logger.debug(f"Statement: {sql_sel}")
    rs: Result = con.execute(sql_sel)
    result = rs.first()

    if not result or not result[colname]:
        return G3Result(4, None)

    return G3Result(0, result[colname])


def chat_user_setng_params(params):
    is_user = 'user_id' in params.keys()
    is_chat = 'chat_id' in params.keys()
    tbl_name = ''
    tg_user_id: int = 0
    tg_chat_id: int = 0
    if is_user:
        tbl_name = 'user_settings'
        tg_user_id = params['user_id']
    if is_chat:
        tbl_name = 'chat_settings'
        tg_chat_id = params['chat_id']
    if is_user and is_chat:
        tbl_name = 'user_chat_settings'
    return is_chat, is_user, tbl_name, tg_chat_id, tg_user_id
