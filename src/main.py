import logging
import os

from dotenv import load_dotenv
from telegram.error import InvalidToken

from src.bot import Bot
from src.config.logger_config import configure_logging

_TOKEN = "GSEM_BOT_TOKEN"
_DEBUG = "DEBUG"

load_dotenv()

if os.environ.get(_DEBUG).lower() == "true":
    configure_logging(is_debug=True)
else:
    configure_logging(is_debug=False)


def main(bot_token):
    bot = Bot(bot_token)
    bot.run_polling()


if __name__ == "__main__":
    try:
        BOT_TOKEN = os.environ.get(_TOKEN)
        logging.warning("Obtained token successfully")
        main(BOT_TOKEN)
    except InvalidToken:
        logging.critical("Error occurred while obtaining Bot token from environment")
