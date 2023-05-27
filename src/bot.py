import logging

from telegram.ext import ApplicationBuilder, CommandHandler

from src.bot_handlers import get_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


class Bot:
    def __init__(self, TOKEN):
        self.TOKEN = TOKEN
        self.application = ApplicationBuilder().token(TOKEN).build()

    def initialize_handlers(self, handlers):
        for handler in handlers:
            self.application.add_handler(handler)

    def build(self):
        handlers = get_handlers()
        self.initialize_handlers(handlers)

    def run_polling(self):
        logging.info("Starting bot in polling mode")
        self.application.run_polling()
