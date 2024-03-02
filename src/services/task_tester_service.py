import subprocess as sp

from src.utils.exceptions import PepTestError, WrongAnswerError
from src.utils.task_answers import get_task_answer

PATH_TO_CMD = "C:\\Windows\\System32\\cmd.exe"


async def run_test(filepath: str, py_filename: str) -> str:
    result_in_bytes = sp.check_output(
        f"python {filepath}", executable=PATH_TO_CMD, shell=True
    )
    string_result = result_in_bytes.decode("utf-8")
    correct_answer = await get_task_answer(py_filename)
    if string_result != correct_answer:
        raise WrongAnswerError(correct_answer, string_result)

    return string_result


async def is_pep8_valid(py_filename: str):
    pass
