async def format_dict_to_string(token_dict: dict) -> str:
    output = ""
    for uid, user in token_dict.items():
        output += uid + " --> \n"
        for k, v in user.items():
            output += f"\t\t {k} : {v}\n"
        output += "\n\n"
    return output
