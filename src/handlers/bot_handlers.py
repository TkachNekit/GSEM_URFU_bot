import datetime
import functools
import logging
import os
import pprint

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from src.services import telegram_services
from src.services.auth_services import (
    download_file,
    generate_tokens_for_users,
    initialize_session,
    is_admin_request,
    upload_tokens_to_db,
)
from src.utils import bot_commands
from src.utils.exceptions import (
    AdminAccessDenied,
    AlreadyUsedToken,
    InvalidDateError,
    InvalidSessionToken,
    NoArgumentsInLogin,
    TooManyArgumentsInLogin,
    WrongDateFormatError,
)
from src.utils.formaters import format_dict_to_string
from src.utils.validators import validate_args, validate_datetime_args

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

_STUDENT_FILE_NAME = "STUDENT_FILE_NAME"
_ADMIN_USERNAMES = "ADMIN_USERNAMES"
STUDENT_FILE_NAME = os.environ.get(_STUDENT_FILE_NAME)
ADMIN_USERNAMES = os.environ.get(_ADMIN_USERNAMES).split(" ")


def get_handlers() -> list:
    return [
        CommandHandler(bot_commands.START, start),
        CommandHandler(bot_commands.LOGIN, login),
        MessageHandler(filters.Document.TEXT, downloader),
    ]


def _response(text_func):
    @functools.wraps(text_func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = await text_func(update, context)
        await telegram_services.response(update, context, text)

    return wrapper


@_response
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    return "Command start was given"


@_response
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    try:
        args = context.args
        await validate_args(args)
        token = args[0]
        await initialize_session(
            token, update.effective_user.id, update.effective_user.username
        )
        return "👍 [Успешная авторизация] 👍"
    except TooManyArgumentsInLogin:
        return "[Ошибка авторизации]    Не был дан токен    Необходимо: /login <TOKEN>"
    except NoArgumentsInLogin:
        return "[Ошибка авторизации]    Не был дан токен    Необходимо: /login <TOKEN>"
    except AlreadyUsedToken:
        return "[Ошибка авторизации]    Был дан токен, который уже был использован"
    except InvalidSessionToken:
        return "[Ошибка авторизации]    Был дан несуществующий токен"
    # except already logged-in user


@_response
async def downloader(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    try:
        if not await is_admin_request(update.effective_user.username, ADMIN_USERNAMES):
            raise AdminAccessDenied
        datetime_arg = update.message.caption.split()
        date = await validate_datetime_args(datetime_arg)
        await download_file(update, context, STUDENT_FILE_NAME)
        token_dict = await generate_tokens_for_users(STUDENT_FILE_NAME, date)
        await upload_tokens_to_db(token_dict)
        output = "👍 [Успешное создание токенов] 👍\n\n\n" + await format_dict_to_string(
            token_dict
        )
        return output
    except AdminAccessDenied:
        return "[Ошибка]    Нет доступа к загрузке файлов с данного аккаунта"
    except TooManyArgumentsInLogin or NoArgumentsInLogin:
        return "[Ошибка]    Дата окончания действия токенов была указана неверно    Необходимо: 01.01.2023"
    except WrongDateFormatError:
        return "[Ошибка]    Дата была дана в неверном формате   Необходимо: 01.01.2023"
    except InvalidDateError:
        return f"[Ошибка]    Была неверно указана дата   \n Указанное число не может быть раньше чем " \
               f"{datetime.datetime.now().date().strftime('%d.%m.%Y')}"
