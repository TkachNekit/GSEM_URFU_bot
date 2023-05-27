import os
import logging

from src.bot import Bot

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.ERROR)
logger = logging.getLogger(__name__)


def main(TOKEN):
    bot = Bot(TOKEN)
    bot.build()
    bot.run_polling()


if __name__ == '__main__':
    try:
        BOT_TOKEN = os.environ.get("GSEM_BOT_TOKEN")
        logger.info("Obtained token successfully")
        main(BOT_TOKEN)
    except KeyError:
        logger.error("Error occured while obtaining Bot's token form environment")
