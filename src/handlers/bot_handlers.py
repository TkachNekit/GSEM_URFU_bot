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
    is_admin_request,
    upload_tokens_to_db, validate_token, logout_user,
)
from src.services.session_services import create_new_session, upload_session_to_db, mark_token_as_used, is_token_used, \
    is_user_logged_in
from src.utils import bot_commands
from src.utils.exceptions import (
    AdminAccessDenied,
    AlreadyUsedToken,
    InvalidDateError,
    InvalidSessionToken,
    NoArgumentsInLogin,
    TooManyArgumentsInLogin,
    WrongDateFormatError, AlreadyLoggedInAccount, LogoutError, WrongPythonFileName,
)
from src.utils.formaters import format_dict_to_string
from src.utils.validators import validate_args, validate_datetime_args, validate_filename

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

_ADMIN_USERNAMES = "ADMIN_USERNAMES"
STUDENT_FILE_NAME = "src/data/students.txt"
ADMIN_USERNAMES = os.environ.get(_ADMIN_USERNAMES).split(" ")


def get_handlers() -> list:
    return [
        CommandHandler(bot_commands.LOGIN, login),
        CommandHandler(bot_commands.LOGOUT, logout),
        MessageHandler(filters.Document.PY, py_downloader),
        MessageHandler(filters.Document.TXT, downloader),
    ]


def _response(text_func):
    @functools.wraps(text_func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = await text_func(update, context)
        await telegram_services.response(update, context, text)

    return wrapper


@_response
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    try:
        args = context.args
        await validate_args(args)
        token = args[0]
        if await validate_token(token):
            raise InvalidSessionToken
        if await is_token_used(token):
            raise AlreadyUsedToken
        if await is_user_logged_in(update.effective_user.username):
            raise AlreadyLoggedInAccount
        session = await create_new_session(token, update.effective_user.username, update.effective_user.id)
        await upload_session_to_db(session)
        await mark_token_as_used(token, update.effective_user.username)
        return "👍 [Успешная авторизация] 👍"
    except TooManyArgumentsInLogin:
        return "[Ошибка авторизации]    Не был дан токен    Необходимо: /login <TOKEN>"
    except NoArgumentsInLogin:
        return "[Ошибка авторизации]    Не был дан токен    Необходимо: /login <TOKEN>"
    except AlreadyUsedToken:
        return "[Ошибка авторизации]    Был дан токен, который уже был использован"
    except InvalidSessionToken:
        return "[Ошибка авторизации]    Был дан несуществующий токен"
    except AlreadyLoggedInAccount:
        return "[Ошибка авторизации]    Пользователь уже авторизован с этого аккаунта"


@_response
async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    return "Ничего не произошло"
    pass
    # try:
    #     if not await is_user_logged_in(update.effective_user.username):
    #         raise LogoutError
    #     await logout_user(update.effective_user.username)
    #
    #     return "👍 [Успешный выход] 👍"
    # except LogoutError:
    #     return "[Ошибка]    Для этой команды необходима авторизация"


@_response
async def downloader(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    try:
        if not await is_admin_request(update.effective_user.username, ADMIN_USERNAMES):
            raise AdminAccessDenied
        date = await validate_datetime_args(update.message.caption)
        await download_file(update, context, STUDENT_FILE_NAME)
        token_dict = await generate_tokens_for_users(STUDENT_FILE_NAME, date)
        await upload_tokens_to_db(token_dict)

        output = "👍 [Успешное создание токенов] 👍\n\n\n" + await format_dict_to_string(
            token_dict
        )
        return output
    except AdminAccessDenied:
        return "[Ошибка]    Нет доступа к загрузке файлов с данного аккаунта"
    except TooManyArgumentsInLogin and NoArgumentsInLogin:
        return "[Ошибка]    Дата окончания действия токенов была указана неверно    Необходимо: 01.01.2023"
    except WrongDateFormatError:
        return "[Ошибка]    Дата была дана в неверном формате   Необходимо: 01.01.2023"
    except InvalidDateError:
        return f"[Ошибка]   Была неверно указана дата   \nУказанное число не может быть раньше чем " \
               f"{datetime.datetime.now().date().strftime('%d.%m.%Y')}"


@_response
async def py_downloader(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    try:
        # проверка названия файла
        print(update.message.document.file_name)
        await validate_filename(update.message.document.file_name)
        file = await context.bot.get_file(update.message.document)
        # получение токена юзера
        # token = await get_current_token_for_user(update.effective_user.username)
        # скачивание ру файла в директорию с токеном
        # file_path = f"src/data/user_exercises{update.message.document.file_name}"
        # await download_file(update, context, file_path)

        # тестирование файла
        # await file.download_to_drive(caption{token}")
        return f"{update.message.document.file_name}"
    except WrongPythonFileName:
        return "[Ошибка отправки]    Неправильное имя файла    Необходимо: task1, или task2, или task3..."
    except TooManyArgumentsInLogin and NoArgumentsInLogin:
        return "[Ошибка]    Был дан неверный заголовок      Необходимо: task1, или task2, или task3..."
