import logging
from typing import Callable, Any, Union

from sqlalchemy import MetaData, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.engine import Result
from sqlalchemy.sql import Select
from sqlalchemy.sql.schema import Table

from converter import ele_ty_converter
from g3b1_cfg.tg_cfg import G3Ctx
from g3b1_data import integrity
from g3b1_data.elements import EleTy, EleVal
from g3b1_data.entities import EntTy
from g3b1_data.model import G3Result
from g3b1_log.log import cfg_logger
from generic_mdl import ele_ty_by_ent_ty

logger = cfg_logger(logging.getLogger(__name__), logging.WARN)


def chat_setting(
        chat_id: int, ele_ty: EleTy, ele_val: str = None) -> dict[str, ...]:
    """Prepare arg dictionary for a setting for the chat_id
    to read or write"""
    params = dict(chat_id=chat_id, colname=ele_ty.col_name, ele_ty=ele_ty)
    if ele_val is not None:
        params['ele_val'] = ele_val
    return params


def user_setting(
        user_id: int, ele_ty: EleTy, ele_val: str = None) -> dict[str, ...]:
    """Prepare arg dictionary for a setting for the user_id
    to read or write"""
    params = dict(user_id=user_id, colname=ele_ty.col_name)
    if ele_val is not None:
        params['ele_val'] = ele_val
    return params


def chat_user_setting(chat_id: int, user_id: int, ele_ty: EleTy, ele_val: str = None) -> dict[str,]:
    """Prepare arg dictionary for a setting for the chat_id/user_id
        to read or write"""
    params = dict(chat_id=chat_id, user_id=user_id, ele_ty=ele_ty)
    if ele_val is not None:
        params['ele_val'] = str(ele_val)
    return params


def cu_setng(ele_ty: EleTy, ele_val: str = None) -> dict[str,]:
    """Prepare arg dictionary for a setting for the chat_id/user_id
        to read or write"""
    params = dict(chat_id=G3Ctx.chat_id(), user_id=G3Ctx.for_user_id(), ele_ty=ele_ty)
    if ele_val is not None:
        params['ele_val'] = str(ele_val)
    return params


def ins_init_setng():
    con: Connection
    user_id = G3Ctx.for_user_id()
    chat_id = G3Ctx.upd.effective_chat.id

    with G3Ctx.eng.begin() as con:
        ext_tg_chat: Table = G3Ctx.md.tables['ext_tg_chat']
        values = dict(id=chat_id)
        ext_insert: insert = insert(ext_tg_chat).values(values).on_conflict_do_update(
            index_elements=['id'],
            set_=values
        )
        con.execute(ext_insert)

        ext_tg_user: Table = G3Ctx.md.tables['ext_tg_user']
        values = dict(id=user_id)
        ext_insert: insert = insert(ext_tg_user).values(values).on_conflict_do_update(
            index_elements=['id'],
            set_=values
        )
        con.execute(ext_insert)

        tbl: Table = G3Ctx.md.tables['user_chat_settings']
        values = {'tg_user_id': user_id, 'tg_chat_id': chat_id}
        ins_stmnt: insert = insert(tbl).values(values).on_conflict_do_update(
            index_elements=values.keys(),
            set_=values
        )
        con.execute(ins_stmnt)


def iup_setng(params: dict[str, ...]) -> dict[str, ...]:
    return iup_setting(G3Ctx.eng, G3Ctx.md, params).result


def iup_setting(con: Union[Connection, Engine], meta_data: MetaData, params: dict[str, ...]) -> G3Result:
    is_chat, is_user, tbl_name, tg_chat_id, tg_user_id = chat_user_setng_params(params)
    values: dict = {}
    index_elements: list = []
    if is_user:
        values = dict(tg_user_id=tg_user_id)
        index_elements.append('tg_user_id')
    if is_chat:
        values['tg_chat_id'] = tg_chat_id
        index_elements.append('tg_chat_id')
    if 'ele_ty' in params.keys():
        ele_ty: EleTy = params['ele_ty']
        if 'ele_val' not in params or params['ele_val'] == 'None':
            values[ele_ty.col_name] = None
        else:
            values[ele_ty.col_name] = params['ele_val']
    tbl_settings: Table = meta_data.tables[tbl_name]

    insert_stmnt: insert = insert(tbl_settings).values(values).on_conflict_do_update(
        index_elements=index_elements,
        set_=values
    )
    logger.debug(f"InsUpd statement: {insert_stmnt}")
    con.execute(insert_stmnt)
    return G3Result(0, params)


def sel_cu_setng_ref_li(con: Connection, meta_data: MetaData, ele_ty: EleTy, ele_val: int) -> list[
    dict[str, ...]]:
    refs_li = []
    tbl_settings: Table = meta_data.tables['user_chat_settings']
    tbl_cols = tbl_settings.columns
    colname = ele_ty.col_name
    sql_sel: Select = select(tbl_cols.tg_chat_id, tbl_cols.tg_user_id)
    sql_sel = sql_sel.where(tbl_cols[colname] == ele_val)
    rs: Result = con.execute(sql_sel)
    row_li = rs.fetchall()
    for row in row_li:
        setng = chat_user_setting(row['tg_chat_id'], row['tg_user_id'], ele_ty)
        refs_li.append(setng)
    return refs_li


def ent_to_setng(ch_us_tup: tuple[int, int], ent: Any, ele_ty: EleTy = None) -> G3Result:
    ent_ty: EntTy = ent.ent_ty()
    if not ele_ty:
        ele_ty = ele_ty_by_ent_ty(ent_ty)
    meta = integrity.meta_by_ent_ty(ent_ty)
    engine = integrity.engine_by_ent_ty(ent_ty)
    with engine.begin() as con:
        g3r = iup_setting(con, meta, chat_user_setting(
            ch_us_tup[0], ch_us_tup[1],
            ele_ty, ent.id_))
        return g3r


def ent_by_setng(ch_us_tup: tuple[int, int], ele_ty: EleTy, sel_cb: Callable = None, ent_ty: EntTy = None) -> G3Result:
    if not ent_ty:
        ent_ty: EntTy = ele_ty.ent_ty
    meta = integrity.meta_by_ent_ty(ent_ty)
    engine = integrity.engine_by_ent_ty(ent_ty)
    with engine.begin() as con:
        ele_val = read_setting(con, meta, chat_user_setting(ch_us_tup[0], ch_us_tup[1], ele_ty))
        g3r = G3Result.from_ele_val(ele_val)
        if g3r.retco != 0:
            return g3r
        if sel_cb:
            return sel_cb(g3r.result)
        else:
            return g3r


@ele_ty_converter()
def read_setng(ele_ty: EleTy) -> EleVal:
    if ele_ty.ele_ty_tup:
        setng_li: list[str] = []
        for i in ele_ty.ele_ty_tup:
            setng_dct = cu_setng(i)
            setng = read_setting(G3Ctx.eng, G3Ctx.md, setng_dct)
            setng_li.append(setng.val)
        return EleVal(ele_ty, tuple(setng_li))
    else:
        setng_dct = cu_setng(ele_ty)
        setng = read_setting(G3Ctx.eng, G3Ctx.md, setng_dct)
        return setng


def read_setting(con: Union[Connection, Engine], meta_data: MetaData, params: dict[str, ...]) -> EleVal:
    """

    Returns:
        object:
    """
    is_chat, is_user, tbl_name, tg_chat_id, tg_user_id = chat_user_setng_params(params)

    tbl_settings: Table = meta_data.tables[tbl_name]
    tbl_cols = tbl_settings.columns
    ele_ty: EleTy = params['ele_ty']
    colname = ele_ty.col_name
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

    if result and result[colname]:
        return EleVal(ele_ty, result[colname])

    return EleVal(ele_ty, '')


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
