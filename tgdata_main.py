import functools
import json
import logging
import traceback
from pydoc import html

from telegram import Message, Update, ParseMode
from telegram.ext import CallbackContext, Updater, CommandHandler, MessageHandler, Filters

import subscribe_db
import tg_db
import utilities
from log.g3b1_log import cfg_logger
from tg_db import tg_db_create_tables, synchronize_from_message
# This can be your own ID, or one for a developer group/channel.
# You can use the /start command of this bot to see your chat id.
from utilities import G3Command, G3Module, module_by_file_str

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
    escaped_error_text = html.escape(tb_string[: 3753])
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{escaped_error_text}</pre>'
    )

    # Finally, send the message
    context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML)


def handler():
    def decorator_handler(hdl_cmd_func):
        @functools.wraps(hdl_cmd_func)
        def wrapper_handler(*arg, **kwargs):
            g3_cmd: G3Command = utilities.g3_cmd_by_func(hdl_cmd_func)
            ctx: CallbackContext = arg[1]
            if not ctx.args:
                ctx.args = []
            # Have kwargs been passed by the caller and are missing in ctx.args?
            # Simple test, i.e. no analysis of possible mismatches
            # A handler method can therefore be called by populating kwargs or ctx.args (in the right order)
            if len(kwargs) > 0 and len(kwargs) > len(ctx.args):
                ctx.args.clear()
                for kw in kwargs:
                    if len(kwargs) == 1:
                        split_li = str(kwargs[kw]).split(' ')
                        ctx.args.extend(split_li)
                    else:
                        ctx.args.append(kwargs[kw])
            idx_last = len(ctx.args) - 1
            for idx, item in enumerate(g3_cmd.args):
                idx_ctx_args = idx - 2
                if idx_ctx_args < 0:
                    pass  # arg position argument
                elif idx_ctx_args >= idx_last:
                    if len(g3_cmd.args) == 3:
                        kwargs.update({item.arg: ''.join(ctx.args)})
                    else:
                        kwargs.update({item.arg: ctx.args[idx_ctx_args]})
                else:
                    kwargs.update({item.arg: None})
            hdl_cmd_func(*arg, **kwargs)

        return wrapper_handler

    return decorator_handler


def start(update: Update, context: CallbackContext) -> None:
    """Displays info on how to trigger an error."""
    tg_db.synchronize_from_message(update.message)
    # @g3b1_todo_bot -> todo
    g3_m_str = update.effective_message.bot.username.split("_")[1]

    commands_str = utilities.build_commands_str(utilities.g3_m_dct[g3_m_str].cmd_dct)
    update.effective_message.reply_html(
        commands_str +
        utilities.build_debug_str(update)
    )


def hdl_message(update: Update, context: CallbackContext) -> None:
    """store message to DB"""
    message = update.message
    logger.debug(f"Handle message {message}")
    tg_db.synchronize_from_message(message)


def start_bot(file: str):  # ,  hdl_for_start: callable = start, hdl_for_message: callable = hdl_message):
    """Run the bot."""
    module_name = module_by_file_str(file)
    g3_m: G3Module
    # =
    utilities.initialize_g3_m_dct(file, eval(f'{utilities.script_by_file_str(file)}'
                                             f'.COLUMNS_{module_name}'))
    g3_m = utilities.g3_m_dct[module_name]
    cmd_dct: dict = g3_m.cmd_dct

    bot_dict: dict = subscribe_db.bot_all()[module_name]
    bot_token = bot_dict['token']

    # Create the Updater and pass it your bot's token.
    updater = Updater(bot_token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register the commands...
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, hdl_message))
    dispatcher.add_handler(CommandHandler('start', start))
    command: G3Command
    for key, command in cmd_dct.items():
        logger.debug(f'Add handler for: {command.name} and {command.long_name}')
        dispatcher.add_handler(CommandHandler(command.name, command.handler))
        dispatcher.add_handler(CommandHandler(command.long_name, command.handler))

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


def persist_tg_data(message: Message) -> None:
    """store message to DB"""
    logger.debug(f"Handle message {message}")
    synchronize_from_message(message)


def main() -> None:
    tg_db_create_tables()


if __name__ == '__tgdata_main__':
    main()
