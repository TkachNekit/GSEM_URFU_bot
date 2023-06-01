import datetime

from src.entities.user import User


class Session:
    def __init__(self, token: str, tg_id: int, tg_username: str, user: User):
        self.telegram_username = tg_username
        self.telegram_id = tg_id
        self.user = user
        self.started_at = datetime.datetime.now().date()
        self.ends_at = user.deadline
        self.token = token
