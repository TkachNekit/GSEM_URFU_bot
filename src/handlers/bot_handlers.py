import datetime
import functools
import logging
import os

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from src.services import telegram_services
from src.services.auth_services import (
    deactivate_session,
    download_py_file,
    download_txt_file,
    generate_tokens_for_users,
    is_admin_request,
    log_in_new_user,
    log_in_user,
    upload_tokens_to_db,
)
from src.services.session_services import (
    create_new_session,
    get_current_token_for_user,
    get_progress,
    is_token_in_use,
    is_user_logged_in,
    mark_progress,
    validate_login,
    was_token_used_before,
)
from src.services.task_tester_service import run_test
from src.utils import bot_commands
from src.utils.exceptions import (
    AdminAccessDenied,
    AlreadyLoggedInAccount,
    InvalidDateError,
    InvalidSessionToken,
    NoActiveSessionError,
    NoArgumentsInLogin,
    PepTestError,
    TokenAlreadyInUseError,
    TokenNotFoundError,
    TooManyArgumentsInLogin,
    WrongAnswerError,
    WrongDateFormatError,
    WrongPythonFileName,
)
from src.utils.formaters import format_dict_to_string, format_progress_to_str
from src.utils.validators import validate_datetime_args, validate_filename

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

_ADMIN_USERNAMES = "ADMIN_USERNAMES"
STUDENT_FILE_NAME = "src/data/students.txt"
ADMIN_USERNAMES = os.environ.get(_ADMIN_USERNAMES).split(" ")


def get_handlers() -> list:
    return [
        CommandHandler(bot_commands.LOGIN, login),
        CommandHandler(bot_commands.LOGIN_STATUS, login_status),
        CommandHandler(bot_commands.PROGRESS, progress),
        CommandHandler(bot_commands.LOGOUT, logout),
        MessageHandler(filters.Document.PY, py_file_handler),
        MessageHandler(filters.Document.TXT, students_downloader),
        CommandHandler(bot_commands.UPLOAD_STUDENT_PROGRESS, upload_student_progress),
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
        username = update.effective_user.username
        tg_id = update.effective_user.id
        token = await validate_login(username, args)
        if await is_token_in_use(token):
            raise TokenAlreadyInUseError
        if await was_token_used_before(token):
            await log_in_user(token, username, tg_id)
        else:
            await log_in_new_user(token, username, tg_id)
        return "👍 [Успешная авторизация] 👍"
    except TooManyArgumentsInLogin:
        return "[Ошибка авторизации]    Не был дан токен    Необходимо: /login <TOKEN>"
    except NoArgumentsInLogin:
        return "[Ошибка авторизации]    Не был дан токен    Необходимо: /login <TOKEN>"
    except TokenAlreadyInUseError:
        return "[Ошибка авторизации]    Был дан токен, под которым уже авторизованы"
    except InvalidSessionToken:
        return "[Ошибка авторизации]    Был дан несуществующий токен"
    except AlreadyLoggedInAccount:
        return "[Ошибка авторизации]    Пользователь уже авторизован с этого аккаунта"


@_response
async def login_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    username = update.effective_user.username
    if await is_user_logged_in(username):
        token = await get_current_token_for_user(username)
        return f'[Статус]    Авторизован под "{token}"'
    else:
        return "[Статус]    Не авторизован"


@_response
async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    try:
        if not await is_user_logged_in(update.effective_user.username):
            raise NoActiveSessionError
        progress_dict = await get_progress(update.effective_user.username)
        return "[Прогресс]\n" + await format_progress_to_str(progress_dict)
    except NoActiveSessionError:
        return "[Ошибка]    Необходима авторизация"


@_response
async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    try:
        username = update.effective_user.username
        await deactivate_session(username)
        return "👍 [Успешный выход] 👍"
    except NoActiveSessionError:
        return "[Ошибка]    Для этой команды необходима авторизация"


@_response
async def students_downloader(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    try:
        if not await is_admin_request(update.effective_user.username, ADMIN_USERNAMES):
            raise AdminAccessDenied
        date = await validate_datetime_args(update.message.caption)
        await download_txt_file(update, context, STUDENT_FILE_NAME)
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
        return (
            f"[Ошибка]   Была неверно указана дата   \nУказанное число не может быть раньше чем "
            f"{datetime.datetime.now().date().strftime('%d.%m.%Y')}"
        )


@_response
async def py_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    try:
        await validate_filename(update.message.document.file_name)
        token = await get_current_token_for_user(update.effective_user.username)
        filepath = await download_py_file(
            update, context, update.message.document.file_name, token
        )
        result = await run_test(filepath, update.message.document.file_name)
        await mark_progress(token, update.message.document.file_name)
        return result + "Это корректный вывод, задача зачтена 👍"
    except WrongPythonFileName:
        return "[Ошибка отправки]    Неправильное имя файла    Необходимо: task1, или task2, или task3..."
    except TooManyArgumentsInLogin and NoArgumentsInLogin:
        return "[Ошибка отправки]    Был дан неверный заголовок      Необходимо: task1, или task2, или task3..."
    except TokenNotFoundError:
        return "[Ошибка]    Невозможно найти токен по вашему профилю"
    except WrongAnswerError:
        return "[Неверный ответ]    Программа выводит неверные данные"
    except PepTestError:
        return "[Неверный ответ]    Программа не прошла PEP8 валидацию"


async def upload_student_progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """FOR ADMIN ONLY! Handler controls uploading students progress to google spreadsheets"""
    pass
