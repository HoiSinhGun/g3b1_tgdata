import json
import logging
import os
import traceback
from pydoc import html

from telegram import Message, Update, ParseMode
from telegram.ext import CallbackContext, Updater, CommandHandler, MessageHandler, Filters

import subscribe_db
from tg_db import tg_db_create_tables, synchronize_from_message

from log.g3b1_log import cfg_logger

# This can be your own ID, or one for a developer group/channel.
# You can use the /start command of this bot to see your chat id.
from utilities import TgCommand, get_module_name

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


def start_bot(file: str, commands: dict, start: callable, hdl_message: callable = None):
    """Run the bot."""
    # my_persistence = PicklePersistence(filename='c:\\dev\\tg\\tg_data.txt')
    module_name = get_module_name(file)
    bot_dict: dict = subscribe_db.bot_all()[module_name]
    bot_token = bot_dict['token']

# Create the Updater and pass it your bot's token.
    updater = Updater(bot_token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register the commands...
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, hdl_message))
    dispatcher.add_handler(CommandHandler('start', start))
    command: TgCommand
    for key, command in commands.items():
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
