import logging

from telegram.ext import ApplicationBuilder

from src.handlers.bot_handlers import get_handlers


class Bot:
    def __init__(self, token):
        self.TOKEN = token
        self.application = ApplicationBuilder().token(token).build()
        handlers = get_handlers()
        self._initialize_handlers(handlers)

    def _initialize_handlers(self, handlers):
        for handler in handlers:
            self.application.add_handler(handler)

    def run_polling(self):
        logging.warning("Starting bot in polling mode")
        self.application.run_polling()
