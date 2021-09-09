import functools
import json
import logging
import traceback
from pydoc import html

from telegram import Update, ParseMode
from telegram.ext import CallbackContext, Updater, CommandHandler, MessageHandler, Filters

from entities import Entity
from g3b1_log.g3b1_log import cfg_logger
# This can be your own ID, or one for a developer group/channel.
# You can use the /start command of this bot to see your chat id.
from g3b1_serv import utilities
from model import *
from subscribe.data import db
from tg_db_sqlite import tg_db_create_tables

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
    message = (
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '\n\n'
        # f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        # f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'{escaped_error_text}</pre>'
    )

    # Finally, send the message
    context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML)


def tg_handler():
    def decorator_handler(cmd_func):
        @functools.wraps(cmd_func)
        def wrapper_handler(*arg, **kwargs):
            """arg should have 2 entries only: upd and ctx
            upd contains user_id and chat_id *required by many handlers, passed depending on funcdef*
            kwargs contains additional hdl specific parameters found.
            Their values are found in ctx.args as well if called from TG API
              """
            upd: Update = arg[0]
            ctx_args = []
            # ctx: CallbackContext = None
            # if len(arg) > 1:
            ctx: CallbackContext = arg[1]
            if ctx and ctx.args:
                ctx_args = ctx.args

            g3_cmd: G3Command = utilities.g3_cmd_by_func(cmd_func)
            # noinspection PyTypeChecker
            ent_ty: Entity = None
            if g3_cmd.arg_req_ent_ty():
                # args extraction for generic commands
                ent_ty = kwargs['ent_ty']
                kwargs.pop('ent_ty')

            # Have kwargs been passed by the caller and are missing in ctx.args?
            # Then we rebuild ctx.args from kwargs
            # Simple g3b1_test, i.e. no analysis of possible mismatches
            # A handler method can therefore be called by populating kwargs or ctx.args (in the right order)
            if len(kwargs) > 0 and len(kwargs) > len(ctx_args):
                ctx_args.clear()
                for kw in kwargs:
                    if len(kwargs) == 1:
                        """This makes no sense, maybe we pass title = 'hello world' and 
                        have then len(ctx.args) == 2 Why should we want this?
                        And the other way around is missing, isn't it?
                        Aha! Check the join part below. Parsing single title alike args with possible spaces 
                        """
                        split_li = str(kwargs[kw]).split(' ')
                        ctx_args.extend(split_li)
                    else:
                        ctx_args.append(kwargs[kw])
            # At this point kwargs could be cleared to ensure
            # same state, no matter where we come from (testcase, TG, click cmd)

            idx_last_ctx_arg = len(ctx_args) - 1
            cmd_arg_li = g3_cmd.extra_args()  # skipping upd, chat_id, user_id
            for idx, item in enumerate(cmd_arg_li):
                if idx <= idx_last_ctx_arg:
                    if len(cmd_arg_li) == 1:
                        # A title like argument with spaces will be split into several args by PTB
                        kwargs.update({item.arg: ' '.join(ctx_args)})
                    else:
                        kwargs.update({item.arg: ctx_args[idx]})
                else:
                    kwargs.update({item.arg: None})

            new_arg_li = [upd]
            chat_id = upd.effective_chat.id
            user_id = upd.effective_user.id
            reply_to_msg = upd.effective_message.reply_to_message
            if g3_cmd.arg_req_ctx():
                new_arg_li.append(ctx)
            if g3_cmd.arg_req_reply_to_msg() or g3_cmd.arg_req_src_msg():
                if g3_cmd.arg_req_reply_to_msg():
                    new_arg_li.append(reply_to_msg)
                if g3_cmd.arg_req_src_msg():
                    src_msg = None
                    if reply_to_msg:
                        src_msg = reply_to_msg
                    else:
                        if utilities.is_msg_w_cmd(upd.effective_message.text):
                            # src_msg is the message assumed to be the input for the command
                            # if no msg has been replied to
                            # it can not be safely guessed to be the latest chat-message
                            src_msg = utilities.read_latest_message(chat_id, user_id)
                    new_arg_li.append(src_msg)
            if g3_cmd.arg_req_reply_to_user_id():
                if reply_to_msg:
                    from_user_id = reply_to_msg.from_user.id
                else:
                    from_user_id = None
                new_arg_li.append(from_user_id)
            if g3_cmd.arg_req_chat():
                new_arg_li.append(chat_id)
            if g3_cmd.arg_req_user():
                new_arg_li.append(user_id)
            if g3_cmd.arg_req_ent_ty():
                new_arg_li.append(ent_ty)
            output = cmd_func(*new_arg_li, **kwargs)
            return output

        return wrapper_handler

    return decorator_handler


def start(upd: Update, ctx: CallbackContext) -> None:
    """Displays info on how to trigger an error."""
    # @g3b1_todo_bot -> todo
    g3_m_str = upd.effective_message.bot.username.split("_")[1]
    if g3_m_str == 'translate':
        g3_m_str = 'trans'

    cmd_scope = ''
    if ctx and ctx.args and len(ctx.args) > 0:
        cmd_scope = ctx.args[0]

    commands_str = utilities.build_commands_str(utilities.g3_m_dct[g3_m_str].cmd_dct, cmd_scope)
    upd.effective_message.reply_html(
        commands_str +
        utilities.build_debug_str(upd)
    )


# noinspection PyUnusedLocal
def hdl_message(upd: Update, ctx: CallbackContext) -> None:
    pass


def start_bot(file: str,
              hdl_for_message: Callable = hdl_message):
    # ,  hdl_for_start: callable = start, hdl_for_message: callable = hdl_message):
    """Run the bot."""
    bot_li: dict[str, dict] = db.bot_all()
    g3_m: G3Module = utilities.g3_m_dct_init(file)
    cmd_dct: dict = g3_m.cmd_dct

    bot_dict: dict = bot_li[g3_m.name]
    bot_token = bot_dict['token']

    # Create the Updater and pass it your bot's token.
    updater = Updater(bot_token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register the commands...

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
