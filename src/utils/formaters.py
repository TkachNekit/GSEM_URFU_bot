async def format_dict_to_string(token_dict: dict) -> str:
    output = ""
    for uid, user in token_dict.items():
        output += uid + " --> \n"
        for k, v in user.items():
            output += f"\t\t {k} : {v}\n"
        output += "\n\n"
    return output


async def format_progress_to_str(progress_dict) -> str:
    if not progress_dict:
        return "Пока не выполнена ни одна задача 😞😞"
    output = ""
    keys = sorted(progress_dict.keys(), key=lambda x: int(x.split('task')[1].split('.py')[0]))
    for k in keys:
        task = k.split(".")[0]
        output += task + "--> Выполнена\n"
    return output
