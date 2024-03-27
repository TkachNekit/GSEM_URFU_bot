from telegram import Update
from telegram.ext import ContextTypes


async def response(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> None:
    if len(text) > 4096:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text[:4096])
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
