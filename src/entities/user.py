import datetime


class User:
    def __init__(
        self, first_name: str, last_name: str, group: str, deadline: datetime.date
    ):
        self.first_name = first_name
        self.last_name = last_name
        self.group = group
        self.deadline = deadline
