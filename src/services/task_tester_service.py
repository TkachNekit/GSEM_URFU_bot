import subprocess as sp

from flake8.api import legacy as flake8

from src.utils.exceptions import PepTestError, WrongAnswerError
from src.utils.task_answers import get_task_answer

PATH_TO_CMD = "C:\\Windows\\System32\\cmd.exe"


async def run_tests(filepath: str, py_filename: str) -> str:
    result_in_bytes = sp.check_output(
        f"python {filepath}", executable=PATH_TO_CMD, shell=True
    )
    string_result = result_in_bytes.decode("utf-8")
    correct_answer = await get_task_answer(py_filename)
    if string_result != correct_answer:
        raise WrongAnswerError(correct_answer, string_result)

    await test_for_pep8(filepath)

    return string_result


async def test_for_pep8(filepath: str):
    # Создаем объект StyleGuide для проверки кода PEP8
    style_guide = flake8.get_style_guide()
    # Загружаем файл и проверяем его на соответствие PEP8
    report = style_guide.check_files(
        [
            filepath,
        ]
    )
    print(report.get_statistics("E"))
    if report.get_statistics("E"):
        raise PepTestError(report.get_statistics("E"))
