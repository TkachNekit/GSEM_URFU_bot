import json
import os
import uuid
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from src.services.session_services import (
    activate_session,
    create_new_session,
    get_current_token_for_user,
    is_user_logged_in,
    mark_token_as_used,
    upload_session_to_db,
)
from src.utils.exceptions import NoActiveSessionError, TokenNotFoundError
from src.utils.namings import SESSION_FILE, TASK_FILEPATH, TOKEN_FILE


async def generate_tokens_for_users(filename: str, date: datetime.date) -> dict:
    token_dict = dict()
    with open(filename, "r", encoding="utf-8") as f:
        while True:
            temp_dic = dict()
            line = f.readline()
            args = line.split()
            if not args:
                break
            temp_dic["last_name"] = args[0]
            temp_dic["first_name"] = args[1]
            temp_dic["group"] = args[2]
            temp_dic["deadline"] = str(date)
            temp_dic["is_in_use"] = False
            temp_dic["telegram_username"] = None
            token = str(uuid.uuid4())
            token_dict[token] = temp_dic
    return token_dict


async def upload_tokens_to_db(token_dict: dict) -> None:
    with open(TOKEN_FILE, "w", encoding="utf-8") as token_file:
        json.dump(
            token_dict,
            token_file,
            sort_keys=False,
            indent=4,
            ensure_ascii=False,
            separators=(",", ": "),
        )


async def create_file(filename) -> None:
    with open(filename, "x") as f:
        f.write("")


async def create_directory(path) -> None:
    os.mkdir(path)


async def download_file(
    update: Update, context: ContextTypes.DEFAULT_TYPE, filename: str, token: str
) -> str:
    path = TASK_FILEPATH
    file = await context.bot.get_file(update.message.document)
    path += token + "/"
    if not os.path.isdir(path):
        await create_directory(path)
    path += filename
    if not os.path.isfile(path):
        await create_file(path)
    await file.download_to_drive(path)
    return path


async def is_admin_request(username: str, admin_list: [str]) -> bool:
    return username in admin_list


async def deactivate_session(username: str) -> None:
    if not await is_user_logged_in(username):
        raise NoActiveSessionError
    token = await get_current_token_for_user(username)
    with open(SESSION_FILE, "r", encoding="utf-8") as session_file:
        session_data = json.load(session_file)
        for session in session_data["sessions"]:
            if token in session.keys():
                session[token]["is_in_progress"] = False
                session[token]["telegram_username"] = None
                session[token]["telegram_id"] = None
    with open(SESSION_FILE, "w", encoding="utf-8") as session_file:
        json.dump(
            session_data,
            session_file,
            sort_keys=False,
            indent=4,
            ensure_ascii=False,
            separators=(",", ": "),
        )
    with open(TOKEN_FILE, "r", encoding="utf-8") as token_file:
        token_data = json.load(token_file)
        token_data[token]["is_in_use"] = False
        token_data[token]["telegram_username"] = None
    with open(TOKEN_FILE, "w", encoding="utf-8") as token_file:
        json.dump(
            token_data,
            token_file,
            sort_keys=False,
            indent=4,
            ensure_ascii=False,
            separators=(",", ": "),
        )


async def log_in_new_user(token: str, username: str, tg_id: int):
    session = await create_new_session(token, username, tg_id)
    await upload_session_to_db(session)
    await mark_token_as_used(token, username)


async def log_in_user(token: str, username: str, tg_id: int):
    await mark_token_as_used(token, username)
    await activate_session(token, username, tg_id)
