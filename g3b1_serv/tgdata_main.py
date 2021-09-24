import importlib
import json
import logging
import traceback
from pydoc import html
from typing import Callable

from sqlalchemy import MetaData
from sqlalchemy.engine import Engine
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from g3b1_cfg.tg_cfg import G3Context, init_g3_m
from g3b1_cfg.tg_cfg import sel_g3_m
from g3b1_data import settings
from g3b1_data.entities import EntTy
from g3b1_data.model import G3Command, G3Module
from g3b1_data.tg_db_sqlite import tg_db_create_tables
from g3b1_log.log import cfg_logger
# This can be your own ID, or one for a developer group/channel.
# You can use the /start command of this bot to see your chat id.
from g3b1_serv import utilities, tg_reply, generic_hdl
from g3b1_ui.model import TgUIC
from subscribe.data import db
from subscribe.serv import services as sub_services

DEVELOPER_CHAT_ID = -579559871

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def error_handler(update: object, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    escaped_error_text = html.escape(tb_string[: 3357])
    # noinspection PyUnusedLocal
    message = (
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '\n\n'
        # f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        # f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'{escaped_error_text}</pre>'
    )

    # Finally, send the message
    # context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML)


def start(upd: Update, ctx: CallbackContext) -> None:
    """Start menu and bot for user activation"""
    G3Context.upd = upd

    # @g3b1_todo_bot -> todo
    g3_m_str = upd.effective_message.bot.username.split("_")[1]
    if g3_m_str == 'translate':
        g3_m_str = 'trans'

    settings.ins_init_setng()
    sub_services.bot_activate(g3_m_str)

    cmd_scope = ''
    if ctx and ctx.args and len(ctx.args) > 0:
        cmd_scope = ctx.args[0]

    commands_str = utilities.build_commands_str(sel_g3_m(g3_m_str).cmd_dct, cmd_scope)
    upd.effective_message.reply_html(
        commands_str +
        utilities.build_debug_str(upd)
    )


# noinspection PyUnusedLocal
def hdl_message(upd: Update, ctx: CallbackContext) -> None:
    pass


@generic_hdl.tg_handler()
def bot(g3_m_str: str, cmd_prefix: str, uname: str) -> None:
    """If given as 1st arg sets the current bot. Otherwise sends a message with inline buttons to select the bot
     If given as 2nd arg sets the cmd_prefix. Otherwise resets the cmd_prefix to empty.
     IF given as 3rd arg the setting will be done for the specified user"""
    if g3_m_str:
        sub_services.iup_setng_cmd_prefix(uname=uname, cmd_prefix=cmd_prefix, g3_m_str=g3_m_str)
        return

    keyboard = [
        [
            InlineKeyboardButton("Translate", callback_data='bot:trans'),
            InlineKeyboardButton("Money", callback_data='bot:money'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    TgUIC.uic.send('Please choose:', reply_markup=reply_markup)


def query_answer(upd: Update, ctx: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    G3Context.upd = upd
    query = upd.callback_query
    qd_split = query.data.split(':', 1)
    g3_m_str = qd_split[0]
    mi_id = qd_split[1]
    g3_m: G3Module = sel_g3_m(g3_m_str)
    sub_services.iup_setng_cmd_prefix(cmd_prefix=mi_id, g3_m_str=g3_m_str)

    if mi_id in g3_m.cmd_dct.keys():
        g3_cmd: G3Command = g3_m.cmd_dct[mi_id]
        sub_services.iup_setng_cmd_default(g3_cmd)
    else:
        sub_services.iup_setng_cmd_default()

    query.answer()
    if mi_id.endswith('33'):
        # list
        ent_str = mi_id[:-3]
        ent_ty = EntTy.by_id(ent_str)
        if ent_ty:
            # Generic list command on entity of type ent_ty
            generic_hdl.cmd_ent_ty_33_li(upd, ctx, ent_ty=ent_ty)
            return

    module = importlib.import_module(f'{g3_m_str}.tg_hdl')
    cmd_menu_func = getattr(module, 'cmd_menu')
    ctx.args = [mi_id]
    cmd_menu_func(upd, ctx)
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery


def go2(upd: Update):
    """
    Start function. Displayed whenever the /start command is called.
    This function sets the language of the bot.
    """
    keyboard = [['<<', '😶', '🤔', '>>'],
                ['❗', '❓', '🔐']]
    message = "Choose an option!"

    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard=True,
                                       resize_keyboard=True)
    tg_reply.send(upd, message, reply_markup=reply_markup)


def start_bot(file: str,
              eng: Engine, md: MetaData,
              hdl_for_message: Callable = hdl_message):
    # ,  hdl_for_start: callable = start, hdl_for_message: callable = hdl_message):
    """Run the bot."""
    G3Context.eng = eng
    G3Context.md = md
    bot_li: dict[str, dict] = db.bot_all()
    g3_m: G3Module = init_g3_m(file)
    cmd_dct: dict = g3_m.cmd_dct

    bot_dict: dict = bot_li[g3_m.name]
    bot_token = bot_dict['token']

    # Create the Updater and pass it your bot's token.
    updater = Updater(bot_token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register the commands...

    # noinspection PyTypeChecker
    dispatcher.add_handler(CommandHandler('bot', bot))
    dispatcher.add_handler(CommandHandler('go2', go2))
    # noinspection PyTypeChecker
    dispatcher.add_handler(CallbackQueryHandler(query_answer))
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, hdl_for_message))
    dispatcher.add_handler(CommandHandler('start', start))
    command: G3Command
    for key, command in cmd_dct.items():
        logger.debug(f'Add handler for: {command.name} and {command.long_name}')
        dispatcher.add_handler(CommandHandler(command.name, command.handler))
        dispatcher.add_handler(CommandHandler(command.long_name, command.handler))
        dispatcher.add_handler(MessageHandler(filter_r_g3cmd(command),
                                              # | Filters.regex(r'^(\.' + command.name + r' .*)$'),
                                              command.handler))

    # ...and the error handler
    logger.debug("add error handler")
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    logger.debug("Start polling:")
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def filter_r_g3cmd(command: G3Command):
    return Filters.regex(r'^(\.' + command.name + r')$')


def main() -> None:
    tg_db_create_tables()


if __name__ == '__main__':
    main()
