import os

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from django.conf import settings


def get_service():
    """
    Получам доступ к гугл таблицам
    """
    creds = None
    if os.path.exists(settings.BASE_DIR / "token.json"):
        creds = Credentials.from_authorized_user_file(settings.BASE_DIR / "token.json", settings.GS_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.BASE_DIR / "credentials.json", settings.GS_SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(settings.BASE_DIR / "token.json", "w") as token:
            token.write(creds.to_json())
    return build('sheets', 'v4', credentials=creds)


def get_main_table_data(sheet_range=""):
    return get_table_data(settings.GS_TABLE_ID, settings.GS_MAIN_SHEET_NAME, sheet_range=sheet_range)


def get_table_data(table_link, sheet_name, sheet_range):
    """
    Получаем данные из таблицы по ссылке и имени листа
    """
    search_range = sheet_name
    if sheet_range:
        search_range = f"{sheet_name}!{sheet_range}"
    service = get_service()
    response = service.spreadsheets().values().get(
        spreadsheetId=table_link,
        range=search_range
    ).execute()
    return response["values"]


def get_project_indexes():
    start_index = 8
    table = get_main_table_data(f"A{start_index}:B")
    project_indexes = dict()
    for i, line in enumerate(table):
        if len(line) == 1 and line[0] == "ИТОГО ПО ВСЕМ:":
            break
        if len(line) == 2:
            project_indexes[line[1]] = i + start_index
    return project_indexes


def write_to_cell_google_sheet(data: str, table_link: str, table_sheet_name: str, cell_id: str):
    """
    Отправляем данные в гугл таблицу по указанному айди таблицы и названию листа
    """
    service = get_service()
    body = {
        "values": [[data]]
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=table_link, range=f"{table_sheet_name}!{cell_id}",
        valueInputOption="USER_ENTERED", body=body).execute()
    return result


def create_sheet_copy(copy_table_id: str, copy_sheet_id: int):
    service = get_service()
    body = {
        "destinationSpreadsheetId": copy_table_id,
    }
    response = service.spreadsheets().sheets().copyTo(
        spreadsheetId=copy_table_id,
        sheetId=copy_sheet_id,
        body=body,
    ).execute()
    return response


def update_sheet_name(sheet_id: int, new_name: str):
    service = get_service()
    body = {
        'requests':
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "title": new_name,
                },
                "fields": "title",
            }
        }
    }
    return service.spreadsheets().batchUpdate(spreadsheetId=settings.GS_TABLE_ID, body=body).execute()


def create_main_sheet_copy(sheet_name: str):
    response = create_sheet_copy(
        settings.GS_TABLE_ID,
        settings.GS_MAIN_SHEET_ID,
    )
    response2 = update_sheet_name(response["sheetId"], sheet_name)
    print(response2)
    return response["sheetId"]




