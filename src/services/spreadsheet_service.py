import gspread
from datetime import datetime
from gspread import Spreadsheet
from gspread.exceptions import APIError

from src.services.session_services import get_user_from_token

PATH = "C:\\Users\\nikit\PycharmProjects\GSEM_URFU_bot\spreadsheets_data\gsembotproject-f2e927905a89.json"
SPREADSHEET_NAME = "Student-Progress"


async def get_spreadsheet() -> Spreadsheet:
    gc = gspread.service_account(filename=PATH)
    return gc.open(SPREADSHEET_NAME)  # долго работает, тормозит работу программы


async def fulfill_worksheets(token_dict: dict) -> None:
    sh = await get_spreadsheet()
    await update_worksheets(token_dict, sh)
    await fulfill_cells(token_dict, sh)


async def update_worksheets(token_dict: dict, sh: Spreadsheet) -> None:
    groups = await get_groups(token_dict)
    worksheets = sh.worksheets()  # долго работает, тормозит работу программы
    titles = [i.title for i in worksheets]
    for group_name in groups:
        if group_name in titles:
            sh.del_worksheet(sh.worksheet(group_name))  # долго работает, тормозит работу программы
        sh.add_worksheet(title=group_name, rows=100, cols=100)  # долго работает, тормозит работу программы


async def fulfill_cells(token_dict: dict, sh: Spreadsheet) -> None:
    try:
        worksheets = sh.worksheets()
        groups_of_students = await get_students_by_groups(token_dict)
        for ws in worksheets:

            ws.update_cell(2, 1, 'Name')

            cell_list = ws.range('B1:AC1')
            for i in range(len(cell_list)):
                cell = cell_list[i]
                value = ''
                if i % 3 == 0:
                    value = f'task{i // 3 + 1}'
                cell.value = value
            ws.update_cells(cell_list)

            cell_list = ws.range('B2:AE2')
            for i in range(len(cell_list)):
                cell = cell_list[i]
                if i % 3 == 0:
                    value = 'Passed'
                elif i % 3 == 1:
                    value = 'Date'
                else:
                    value = 'Log'
                cell.value = value
            ws.update_cells(cell_list)

            student_list = groups_of_students[ws.title]
            ws.update(student_list, f'A3:A{len(student_list) + 3}')
            ws.format('A1:AE2', {'textFormat': {'bold': True}})

    except APIError as e:
        raise e


async def get_students_by_groups(token_dict: dict) -> dict:
    output_dic = dict()
    for student in token_dict.values():
        group = student['group']
        if group not in output_dic:
            output_dic[group] = []
        output_dic[group].append([f"{student['last_name']} {student['first_name']}"])
    return output_dic


async def mark_progress_in_google(token: str, filename: str, is_answer_right: bool, is_pep_valid: bool) -> None:
    try:
        user = await get_user_from_token(token)
        sh = await get_spreadsheet()
        worksheet = sh.worksheet(user.group)
        name_cell = worksheet.find(f"{user.last_name} {user.first_name}")
        task_cell = worksheet.find(filename.split('.')[0])

        # Get the current date and time
        current_date_time = datetime.now()
        # Format the current date in the "day.month.year" format
        formatted_date = current_date_time.strftime("%d.%m.%Y")

        if is_answer_right and is_pep_valid:
            worksheet.update_cell(name_cell.row, task_cell.col, '\'+')
            worksheet.update_cell(name_cell.row, task_cell.col + 1, formatted_date)
            worksheet.update_cell(name_cell.row, task_cell.col + 2, "Answer: +\nPep: +")
        elif is_answer_right and not is_pep_valid:
            worksheet.update_cell(name_cell.row, task_cell.col, '-')
            worksheet.update_cell(name_cell.row, task_cell.col + 1, formatted_date)
            worksheet.update_cell(name_cell.row, task_cell.col + 2, "Answer: +\nPep: -")
        elif not is_answer_right and not is_pep_valid:
            worksheet.update_cell(name_cell.row, task_cell.col, '-')
            worksheet.update_cell(name_cell.row, task_cell.col + 1, formatted_date)
            worksheet.update_cell(name_cell.row, task_cell.col + 2, "Answer: -\nPep: -")

    except APIError as e:
        raise e


async def get_groups(token_dict: dict) -> list:
    return list(set([v['group'] for v in token_dict.values()]))
