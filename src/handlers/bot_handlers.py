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
    upload_tokens_to_db, get_new_file_name,
)
from src.services.session_services import (
    create_new_session,
    get_current_token_for_user,
    get_progress,
    is_token_in_use,
    is_user_logged_in,
    mark_progress,
    validate_login,
    was_token_used_before, is_token_valid,
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
    args = context.args
    username = update.effective_user.username
    tg_id = update.effective_user.id

    try:
        token = await validate_login(username, args)

        if await is_token_in_use(token):
            raise TokenAlreadyInUseError

        if await was_token_used_before(token):
            await log_in_user(token, username, tg_id)

        else:
            logging.info(f"User \'{username}\' successfully authorized.")
            await log_in_new_user(token, username, tg_id)

        return "👍 [Успешная авторизация] 👍"

    except Exception as e:
        if isinstance(e, TooManyArgumentsInLogin):
            logging.error(f"User \'{username}\' unsuccessfully tried to authorize. Too many arguments were given.")
            message = "[Ошибка авторизации]    Токен был передан неверно    Необходимо: /login <TOKEN>"

        elif isinstance(e, NoArgumentsInLogin):
            logging.error(f"User \'{username}\' unsuccessfully tried to authorize. No arguments were given.")
            message = "[Ошибка авторизации]    Не был дан токен    Необходимо: /login <TOKEN>"

        elif isinstance(e, TokenAlreadyInUseError):
            logging.error(f"User \'{username}\' unsuccessfully tried to authorize. Token is already in use.")
            message = "[Ошибка авторизации]    Был дан токен, под которым уже авторизованы"

        elif isinstance(e, InvalidSessionToken):
            logging.error(f"User \'{username}\' unsuccessfully tried to authorize. Invalid token were given.")
            message = "[Ошибка авторизации]    Был дан несуществующий токен"

        elif isinstance(e, AlreadyLoggedInAccount):
            logging.error(f"User \'{username}\' unsuccessfully tried to authorize. User already authorized.")
            message = "[Ошибка авторизации]    Пользователь уже авторизован с этого аккаунта"

        else:
            logging.error(f"User tried to login and unpredicted error happened. Error: {e}")
            message = "[Ошибка авторизации]    Произошла непредвиденная ошибка при авторизации. " \
                      "Сообщите преподавателю и попробуйте повторить действие позже."

        return message


@_response
async def login_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    username = update.effective_user.username

    try:
        if not await is_user_logged_in(username):
            raise NoActiveSessionError

        token = await get_current_token_for_user(username)
        logging.info(f"User \'{username}\' successfully requested login status.")
        return f'[Статус]    Авторизован под "{token}".'

    except TokenNotFoundError:
        logging.error(
            f"User \'{username}\' unsuccessfully requested login status. Token not found for the user profile.")
        return "[Ошибка аутентификации]    Невозможно найти токен по вашему профилю."
    except NoActiveSessionError:
        logging.error(f"User \'{username}\' unsuccessfully requested login status. User is not authorized.")
        return "[Ошибка]    Необходима авторизация."


@_response
async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    username = update.effective_user.username

    try:
        if not await is_user_logged_in(username):
            raise NoActiveSessionError

        progress_dict = await get_progress(username)
        logging.info(f"User \'{username}\' successfully requested his progress on tasks.")

        progress_str = await format_progress_to_str(progress_dict)
        return "[Прогресс]\n" + progress_str

    except NoActiveSessionError:
        logging.error(f"User \'{username}\' unsuccessfully requested his progress on tasks. User is not authorized.")
        return "[Ошибка]    Необходима авторизация."


@_response
async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    username = update.effective_user.username

    try:
        await deactivate_session(username)
        logging.info(f"User \'{username}\' successfully logged out.")
        return "👍 [Успешный выход] 👍"

    except NoActiveSessionError:
        logging.error(f"User \'{username}\' unsuccessfully tried to log out. User is not authorized.")
        return "[Ошибка]    Для этой команды необходима авторизация."


@_response
async def students_downloader(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """FOR ADMIN ONLY! Handler controls uploading students to data and gives each user token"""

    username = update.effective_user.username

    try:
        if not await is_admin_request(username, ADMIN_USERNAMES):
            raise AdminAccessDenied

        date = await validate_datetime_args(update.message.caption)
        await download_txt_file(update, context, STUDENT_FILE_NAME)

        token_dict = await generate_tokens_for_users(STUDENT_FILE_NAME, date)
        await upload_tokens_to_db(token_dict)

        output = "👍 [Успешное создание токенов] 👍\n\n\n" + await format_dict_to_string(token_dict)
        logging.warning(f"User \'{username}\' successfully uploaded users' list.")
        return output

    except AdminAccessDenied:
        logging.error(
            f"User \'{username}\' unsuccessfully tried to upload users' list. User doesn't have admin status")
        return "[Ошибка]    Нет доступа к загрузке файлов с данного аккаунта."

    except TooManyArgumentsInLogin and NoArgumentsInLogin:
        logging.error(f"User \'{username}\' unsuccessfully tried to uploaded users' list. Wrong arguments.")
        return "[Ошибка]    Дата окончания действия токенов была указана неверно    Необходимо: 01.01.2023"

    except WrongDateFormatError:
        logging.error(f"User \'{username}\' unsuccessfully tried to uploaded users' list. Wrong date format.")
        return "[Ошибка]    Дата была дана в неверном формате   Необходимо: 01.01.2023"

    except InvalidDateError:
        logging.error(f"User \'{username}\' unsuccessfully tried to uploaded users' list. Wrong date.")
        return (
            f"[Ошибка]   Была неверно указана дата   \nУказанное число не может быть раньше чем "
            f"{datetime.datetime.now().date().strftime('%d.%m.%Y')}")


@_response
async def py_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Function is called when .py file is sent.
    Checks if the user is valid, validates the filename, downloads the .py file, and runs tests"""

    username = update.effective_user.username
    received_file_name = update.message.document.file_name

    try:
        logging.warning(f"Received {received_file_name} file from user {username}")

        token = await get_current_token_for_user(username)
        if not await is_token_valid(token):
            raise TokenNotFoundError
        logging.warning(f"Successfully got token {token} for user {username}")

        await validate_filename(received_file_name)
        logging.warning(f"File {received_file_name} from user {username} has a valid filename")

        new_file_name = await get_new_file_name(received_file_name, token)
        filepath = await download_py_file(update, context, new_file_name, token)
        logging.warning(f"Downloaded user's file {received_file_name} as {token}\\{new_file_name}")

        result = await run_test(filepath, received_file_name)
        logging.warning(f"User's {username} task {new_file_name} successfully passed tests")

        await mark_progress(token, received_file_name)
        return result + "\nЭто корректный вывод, задача зачтена 👍"

    except Exception as e:
        if isinstance(e, WrongAnswerError):
            logging.error(f"User's {username} file {received_file_name} returns wrong answer. "
                          f"Expected result \n {e.correct_result} but got \n {e.user_result}")
            msg = "[Неверный ответ]    Программа выводит неверные данные."

        elif isinstance(e, PepTestError):
            logging.error(f"User's {username} file {received_file_name} couldn't pass PEP tests")
            msg = "[Неверный ответ]    Программа не прошла PEP8 валидацию.",

        elif isinstance(e, WrongPythonFileName):
            logging.error(f"User {username} tried to send file with wrong file_name - {received_file_name}")
            msg = "[Ошибка отправки]    Неправильное имя файла    Необходимо: task1.py, или task2.py, или task3.py ..."

        elif isinstance(e, TokenNotFoundError):
            logging.error(f"Couldn't get token for user {username}")
            msg = "[Ошибка аутентификации]    Невозможно найти токен по вашему профилю."

        elif isinstance(e, OSError):
            logging.critical("OSError was caught, most likely there is no empty space on disk")
            msg = "[Ошибка на сервере]    Произошла непредвиденная ошибка. Сообщите преподавателю о ней."

        elif e.returncode == 1:
            logging.error(f"User {username} sent file {received_file_name}. Error : {e}")
            msg = "[Ошибка исполнения программы]    Файл с программой запускается с ошибкой:\n\n" \
                  f"{str(e).split('/')[-1]}"
        else:
            logging.error(f"User {username} encountered an error: {e}")
            msg = "[Ошибка авторизации]    Произошла непредвиденная ошибка при авторизации. " \
                  "Сообщите преподавателю и попробуйте повторить действие позже."
        return msg


async def upload_student_progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """FOR ADMIN ONLY! Handler controls uploading students progress to google spreadsheets"""
    pass
