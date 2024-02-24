import logging
import os
from dotenv import load_dotenv
from telegram.error import InvalidToken

from src.bot import Bot

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.ERROR
)
logger = logging.getLogger(__name__)

load_dotenv()
_TOKEN = "GSEM_BOT_TOKEN"


def main(bot_token):
    bot = Bot(bot_token)
    bot.run_polling()


if __name__ == "__main__":
    try:
        logger.info("Obtained token successfully")
        BOT_TOKEN = os.environ.get(_TOKEN)
        main(BOT_TOKEN)
    except InvalidToken:
        logger.error("Error occurred while obtaining Bot token form environment")
