from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src import bot_commands


def get_handlers():
    return [
        CommandHandler(bot_commands.START, start),
    ]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_user.id, text="Command start was given"
    )
