import json
import os
import uuid
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from src.utils.exceptions import TokenNotFoundError

TOKEN_FILE = "src/data/tokens.json"
SESSION_FILE = "src/data/sessions.json"
TASK_FILEPATH = "src/data/users_exercises/"


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


async def validate_token(token: str) -> bool:
    with open(TOKEN_FILE, "r", encoding="utf-8") as token_file:
        data = json.load(token_file)
        return not (token in data.keys())


async def get_current_token_for_user(username: str) -> str:
    output_token = None
    with open(SESSION_FILE, "r", encoding="utf-8") as session_file:
        data = json.load(session_file)
        for session in data["sessions"]:
            token = list(session.keys())[0]
            if session[token]["telegram_username"] == username and session[token]["is_in_progress"]:
                output_token = token
    if not output_token:
        raise TokenNotFoundError
    return output_token


async def logout_user(username: str):
    pass
    # user_token = None
    #
    # with open(SESSION_FILE, "r", encoding="utf-8") as session_file:
    #     session_data = json.load(session_file)
    #     sessions_list = session_data["sessions"]
    #     async for session in sessions_list:
    #         token = list(session.keys())[0]
    #         if session[token]["telegram_username"] == username and session[token]["is_in_progress"]:
    #             session[token]["is_in_progress"] = False
    #     se
