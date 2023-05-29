class TooManyArgumentsInLogin(Exception):
    """Raised when user tries to log in and gives too many arguments"""

    pass


class NoArgumentsInLogin(Exception):
    """Raised when user tries to log in and gives no arguments"""

    pass


class AlreadyUsedToken(Exception):
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
