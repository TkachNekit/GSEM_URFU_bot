import json
import logging
from datetime import datetime

from src.entities.session import Session
from src.entities.user import User
from src.utils.exceptions import AlreadyLoggedInAccount, InvalidSessionToken, NoActiveSessionError, TokenNotFoundError
from src.utils.namings import SESSION_FILE, TOKEN_FILE
from src.utils.validators import validate_token_args


async def create_new_session(token: str, username: str, id: int) -> Session:
    try:
        user = await get_user_from_token(token)
        return Session(token, id, username, user)

    except FileNotFoundError:
        # Обработка ошибки, если файл не найден
        raise FileNotFoundError(
            f'Couldn\'t get user from token "{token}". Token-file "{TOKEN_FILE}" not found'
        )

    except json.JSONDecodeError:
        # Обработка ошибки декодирования JSON
        raise ValueError(
            f'Couldn\'t get user from token "{token}". Couldn\'t decode token-file "{TOKEN_FILE}" as JSON'
        )

    except KeyError:
        raise InvalidSessionToken


async def get_user_from_token(token: str) -> User:
    try:
        with open(TOKEN_FILE, encoding="utf-8") as token_file:
            data = json.load(token_file)
            token_data = data[token]
            return User(
                token_data["first_name"],
                token_data["last_name"],
                token_data["group"],
                datetime.strptime(token_data["deadline"], "%Y-%m-%d"),
            )

    except FileNotFoundError:
        # Обработка ошибки, если файл не найден
        raise FileNotFoundError(
            f'Couldn\'t get user from token "{token}". Token-file "{TOKEN_FILE}" not found'
        )

    except json.JSONDecodeError:
        # Обработка ошибки декодирования JSON
        raise ValueError(
            f'Couldn\'t get user from token "{token}". Couldn\'t decode token-file "{TOKEN_FILE}" as JSON'
        )

    except KeyError:
        raise InvalidSessionToken


async def is_token_in_use(token: str) -> bool:
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as token_file:
            data = json.load(token_file)
            if data[token]["is_in_use"]:
                return True
        return False
    except FileNotFoundError:
        # Обработка ошибки, если файл не найден
        logging.error(
            f'Couldn\'t check if token "{token}" is in use. Couldn\'t find token-file on path "{TOKEN_FILE}"'
        )
        return False
    except json.JSONDecodeError:
        # Обработка ошибки декодирования JSON
        logging.error(
            f'Couldn\'t check if token "{token}" is in use. Couldn\'t decode token-file "{TOKEN_FILE}" as JSON'
        )
        return False


async def was_token_used_before(token: str) -> bool:
    with open(SESSION_FILE, "r", encoding="utf-8") as session_file:
        data = json.load(session_file)
        session_list = data["sessions"]
        for session in session_list:
            if token in session.keys():
                return True
        return False


async def validate_login(username: str, args: list) -> str:
    if await is_user_logged_in(username):
        raise AlreadyLoggedInAccount
    await validate_token_args(args)
    token = args[0]
    if not await is_token_valid(token):
        raise InvalidSessionToken
    return token


async def is_token_valid(token: str) -> bool:
    with open(TOKEN_FILE, "r", encoding="utf-8") as token_file:
        data = json.load(token_file)
        return token in data.keys()


async def upload_session_to_db(session: Session) -> None:
    with open(SESSION_FILE, "r", encoding="utf-8") as session_file:
        data = json.load(session_file)
        dic = dict()
        dic[session.token] = {
            "first_name": session.user.first_name,
            "last_name": session.user.last_name,
            "group": session.user.group,
            "telegram_id": session.telegram_id,
            "telegram_username": session.telegram_username,
            "started_at": str(session.started_at),
            "deadline": str(session.ends_at),
            "is_in_progress": True,
            "progress": {},
        }
        data["sessions"].append(dic)
    with open(SESSION_FILE, "w", encoding="utf-8") as outfile:
        json.dump(
            data,
            outfile,
            sort_keys=False,
            indent=4,
            ensure_ascii=False,
            separators=(",", ": "),
        )


async def mark_token_as_used(token: str, telegram_username: str) -> None:
    with open(TOKEN_FILE, "r", encoding="utf-8") as in_file:
        data = json.load(in_file)
        token_data = data[token]
        token_data["telegram_username"] = telegram_username
        token_data["is_in_use"] = True
        data[token] = token_data
    with open(TOKEN_FILE, "w", encoding="utf-8") as outfile:
        json.dump(
            data,
            outfile,
            sort_keys=False,
            indent=4,
            ensure_ascii=False,
            separators=(",", ": "),
        )


async def is_user_logged_in(username: str) -> bool:
    with open(SESSION_FILE, "r", encoding="utf-8") as session_file:
        session_list = json.load(session_file)["sessions"]
        for session in session_list:
            token = list(session.keys())[0]
            if (
                    session[token]["telegram_username"] == username
                    and session[token]["is_in_progress"] is True
            ):
                return True
    return False


async def mark_progress_in_db(token: str, filename: str) -> None:
    with open(SESSION_FILE, "r", encoding="utf-8") as session_file:
        data = json.load(session_file)
        for session in data["sessions"]:
            if token in session.keys():
                session[token]["progress"][filename] = True
    with open(SESSION_FILE, "w", encoding="utf-8") as session_file:
        json.dump(
            data,
            session_file,
            sort_keys=False,
            indent=4,
            ensure_ascii=False,
            separators=(",", ": "),
        )


async def get_current_token_for_user(username: str) -> str:
    output_token = None
    with open(SESSION_FILE, "r", encoding="utf-8") as session_file:
        data = json.load(session_file)
        for session in data["sessions"]:
            token = list(session.keys())[0]
            if (
                    session[token]["telegram_username"] == username
                    and session[token]["is_in_progress"]
            ):
                output_token = token
    if not output_token:
        raise TokenNotFoundError
    return output_token


async def get_progress(username: str) -> dict:
    token = await get_current_token_for_user(username)
    with open(SESSION_FILE, "r", encoding="utf-8") as session_file:
        data = json.load(session_file)
        for session in data["sessions"]:
            if token in session.keys():
                return session[token]["progress"]
    raise NoActiveSessionError


async def activate_session(token: str, username: str, telegram_id: int) -> None:
    with open(SESSION_FILE, "r", encoding="utf-8") as session_file:
        data = json.load(session_file)
        for session in data["sessions"]:
            if token in session.keys():
                session[token]["telegram_id"] = telegram_id
                session[token]["telegram_username"] = username
                session[token]["is_in_progress"] = True
    with open(SESSION_FILE, "w", encoding="utf-8") as session_file:
        json.dump(
            data,
            session_file,
            sort_keys=False,
            indent=4,
            ensure_ascii=False,
            separators=(",", ": "),
        )


async def is_task_done_already(token: str, file_name: str) -> bool:
    with open(SESSION_FILE, "r", encoding="utf-8") as session_file:
        data = json.load(session_file)
        for session in data["sessions"]:
            if token in session.keys():
                progress = session[token]["progress"]
                if file_name in progress.keys():
                    return True
                else:
                    return False
    raise NoActiveSessionError
