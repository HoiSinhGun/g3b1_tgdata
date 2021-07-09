from telegram import Update


def command_successful(update: Update):
    update.effective_message.reply_html(
        f'Command successful!'
    )


def main():
    pass


if __name__ == '__main__':
    main()


def no_data(update: Update) -> None:
    update.effective_message.reply_html(
        'No data found. Try /create <title/bkey>'
    )
    return