from datetime import datetime

from src.utils.exceptions import (
    InvalidDateError,
    NoArgumentsInLogin,
    TooManyArgumentsInLogin,
    WrongDateFormatError,
)


async def validate_args(args) -> None:
    if len(args) > 1:
        raise TooManyArgumentsInLogin
    elif len(args) < 1:
        raise NoArgumentsInLogin


async def validate_datetime_args(args) -> datetime.date:
    if len(args) > 1:
        raise TooManyArgumentsInLogin
    elif len(args) < 1:
        raise NoArgumentsInLogin
    try:
        date = datetime.strptime(args[0], "%d.%m.%Y").date()
        assert date >= datetime.today().date()
        return date
    except ValueError:
        raise WrongDateFormatError
    except AssertionError:
        raise InvalidDateError
