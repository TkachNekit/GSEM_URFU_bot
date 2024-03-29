class TooManyArgumentsInLogin(Exception):
    """Raised when user tries to log in and gives too many arguments"""

    pass


class NoArgumentsInLogin(Exception):
    """Raised when user tries to log in and gives no arguments"""

    pass


class TokenAlreadyInUseError(Exception):
    """Raised when user gives already used token"""

    pass


class InvalidSessionToken(Exception):
    """Raised when user gives invalid token to initialize session"""

    pass


class AdminAccessDenied(Exception):
    """Raised when user tries to access admin commands"""

    pass


class WrongDateFormatError(Exception):
    """Raised when user gives date in wrong format"""

    pass


class InvalidDateError(Exception):
    """Raised when user gives date which is not in the future"""

    pass


class AlreadyLoggedInAccount(Exception):
    """Raised when user tries to log in few times"""

    pass


class WrongPythonFileName(Exception):
    """Raised when user gives a python file with a wrong name"""

    pass


class TokenNotFoundError(Exception):
    """Raised when username was given which doesn't have any active tokens"""

    pass


class WrongAnswerError(Exception):
    """Raised when user task failed test due to wrong answer"""

    def __init__(self, correct_result, user_result):
        self.correct_result = correct_result
        self.user_result = user_result


class PepTestError(Exception):
    """Raised when user task failed test due to pep8 validation"""

    def __init__(self, violation_list: list):
        self.violation_list = violation_list


class NoActiveSessionError(Exception):
    """Raised when logged-out user tries to use command for logged-in users only"""

    pass


class AlreadyDoneTask(Exception):
    """Raised when user tries to pass already done task"""
