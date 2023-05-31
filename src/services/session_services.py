import json
from datetime import datetime

from src.entities.session import Session
from src.entities.user import User
from src.services.auth_services import TOKEN_FILE, SESSION_FILE
from src.utils.exceptions import InvalidSessionToken, AlreadyUsedToken


async def create_new_session(token: str, username: str, id: int) -> Session:
    user = await get_user_from_token(token)
    return Session(token, id, username, user)


async def get_user_from_token(token: str) -> User:
    try:
        with open(TOKEN_FILE, encoding="utf-8") as token_file:
            data = json.load(token_file)
            token_data = data[token]
            return User(
                token_data["first_name"],
                token_data["last_name"],
                token_data["group"],
                datetime.strptime(token_data['deadline'], "%Y-%m-%d")
            )
    except KeyError:
        raise InvalidSessionToken


async def is_token_used(token: str) -> bool:
    with open(TOKEN_FILE, "r", encoding="utf-8") as token_file:
        data = json.load(token_file)
        if data[token]["is_in_use"]:
            return True
    return False


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
            "progress": {}
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
    with open(TOKEN_FILE, "r", encoding='utf-8') as in_file:
        data = json.load(in_file)
        token_data = data[token]
        token_data["telegram_username"] = telegram_username
        token_data["is_in_use"] = True
        data[token] = token_data
    with open(TOKEN_FILE, "w", encoding="utf-8") as outfile:
        json.dump(data,
                  outfile,
                  sort_keys=False,
                  indent=4,
                  ensure_ascii=False,
                  separators=(",", ": "),
                  )


async def is_user_logged_in(username: str):
    with open(SESSION_FILE, "r", encoding="utf-8") as session_file:
        session_list = json.load(session_file)["sessions"]
        for session in session_list:
            token = list(session.keys())[0]
            if session[token]["telegram_username"] == username:
                return True
    return False
