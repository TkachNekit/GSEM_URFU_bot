import datetime

from src.entities.user import User


class Session:
    def __init__(self, token: str, user: User, tg_id: int, tg_username: str):
        self.started_at = datetime.datetime.now()
        self.ends_at = self.started_at + datetime.timedelta(minutes=90)
        self.token = token
        self.user = user
        self.telegram_id = tg_id
        self.telegram_username = tg_username
