import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_PATH = (
    "C:\\Users\\nikit\PycharmProjects\GSEM_URFU_bot\spreadsheets_data\credentials.json"
)
TOKEN_PATH = (
    "C:\\Users\\nikit\PycharmProjects\GSEM_URFU_bot\spreadsheets_data\\token.json"
)
SPREADSHEET_ID = "1mSuIvEQ7fKUa2u918MGhKLhrt-SRAOTuOnlQqZRkgM0"

# async def main():
#     credentials = None
#     if os.path.exists(TOKEN_PATH):
#         credentials = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
#     if not credentials or not credentials.valid:
#         if credentials and credentials.expired and credentials.refresh_token:
#             credentials.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
#             credentials = flow.run_local_server(port=0)
#         with open(TOKEN_PATH, "w") as token:
#             token.write(credentials.to_json())
#
#     try:
#         service = build("sheets", "v4", credentials=credentials)
#         sheets = service.spreadsheets()
#         result = sheets.values().get(spreadsheetId=SPREADSHEET_ID, range="КН-204!A2:M5").execute()
#         values = result.get("values", [])
#
#         for row in values:
#             last_name, first_name = row[0].split()
#             await get_user_progress(last_name, first_name)
#
#     except HttpError as error:
#         print(error)
#
#
# if __name__ == "__main__":
#     await main()
