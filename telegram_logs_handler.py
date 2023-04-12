import logging


class TelegramLogsHandler(logging.Handler):

    def __init__(self, notify_bot, chat_id):
        super().__init__()
        self.bot = notify_bot
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        self.bot.send_message(chat_id=self.chat_id, text=log_entry)
