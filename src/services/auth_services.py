import json
import uuid
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from src.entities.session import Session
from src.entities.user import User
from src.utils.exceptions import AlreadyUsedToken, InvalidSessionToken


async def initialize_session(token: str, tg_id: int, tg_username: str) -> None:
    await _validate_token(token)
    user = await _get_user_from_token(token)
    session = Session(token, user, tg_id, tg_username)
    await _upload_session_to_db(session)


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
            token = str(uuid.uuid4())
            token_dict[token] = temp_dic
    return token_dict


async def upload_tokens_to_db(token_dict: dict) -> None:
    with open("tokens.json", "w", encoding="utf-8") as token_file:
        json.dump(
            token_dict,
            token_file,
            sort_keys=False,
            indent=4,
            ensure_ascii=False,
            separators=(",", ": "),
        )


async def download_file(
    update: Update, context: ContextTypes.DEFAULT_TYPE, filename: str
) -> None:
    file = await context.bot.get_file(update.message.document)
    await file.download_to_drive(filename)


async def is_admin_request(username: str, admin_list: [str]) -> bool:
    return username in admin_list


async def _validate_token(token: str) -> None:
    try:
        with open("tokens.json", "r", encoding="utf-8") as token_file:
            data = json.load(token_file)
            token_data = data[token]
            if not token_data["is_fresh"]:
                raise AlreadyUsedToken
    except KeyError:
        raise InvalidSessionToken


async def _get_user_from_token(token: str) -> User:
    try:
        with open("tokens.json", encoding="utf-8") as token_file:
            data = json.load(token_file)
            token_data = data[token]
            user = User(
                token_data["first_name"], token_data["last_name"], token_data["group"]
            )
            return user
    except KeyError:
        raise InvalidSessionToken


async def _upload_session_to_db(session: Session) -> None:
    pass


#     data = {
#         session.token: {
#             "telegram_id": session.telegram_id,
#             "telegram_username": session.telegram_username,
#             "first_name": session.user.first_name,
#             "last_name": session.user.last_name,
#             "group": session.user.group,
#             "started_at": session.started_at,
#             "ends_at": session.ends_at
#         }}
#     # try:
#     # with open("sessions.json", "w", encoding="utf-8") as session_file:
