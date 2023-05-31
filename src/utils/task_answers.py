answer_bank_account = dict()
answer_bank_account["task1"] = "5\r\n10\r\n"
answer_bank_account["task2"] = "5\r\n15\r\n5\r\n20.0\r\n10.0\r\n"
answer_bank_account["task3"] = "Володя\r\nВолодя из группы ЭУ-210212\r\n"
answer_bank_account["task4"] = "2469108642\r\n"
answer_bank_account["task5"] = "28294\r\n"
answer_bank_account["task6"] = "1.8963931992918867e+46\r\n"
answer_bank_account["task7"] = "0\r\n"
answer_bank_account["task8"] = "-25\r\n"
answer_bank_account["task9"] = "True\r\nFalse\r\nFalse\r\nTrue\r\n"
answer_bank_account["task10"] = "True\r\nFalse\r\n"
answer_bank_account["task11"] = "8\r\n"


async def get_task_answer(task_file: str):
    task_number = task_file.split('.')[0]
    return answer_bank_account[task_number]
