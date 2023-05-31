import re
from datetime import datetime

from src.utils.exceptions import (
    InvalidDateError,
    NoArgumentsInLogin,
    TooManyArgumentsInLogin,
    WrongDateFormatError, WrongPythonFileName,
)

EXERCISE_FILENAME_PATTERN = "^task\d+\.py$"


async def validate_args(args) -> None:
    if len(args) > 1:
        raise TooManyArgumentsInLogin
    elif len(args) < 1:
        raise NoArgumentsInLogin


async def validate_datetime_args(caption) -> datetime.date:
    try:
        args = caption.split()
        if len(args) > 1:
            raise TooManyArgumentsInLogin
        elif len(args) < 1:
            raise NoArgumentsInLogin
        date = datetime.strptime(args[0], "%d.%m.%Y").date()
        assert date >= datetime.today().date()
        return date
    except ValueError:
        raise WrongDateFormatError
    except AssertionError:
        raise InvalidDateError
    except AttributeError:
        raise NoArgumentsInLogin


async def validate_filename(filename):
    pat = re.compile(EXERCISE_FILENAME_PATTERN)
    if not pat.match(filename):
        raise WrongPythonFileName
