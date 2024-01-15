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


def get_table_data(table_link, sheet_name):
    """
    Получаем данные из таблицы по ссылке и имени листа
    """
    service = get_service()
    response = service.spreadsheets().values().get(
        spreadsheetId=table_link,
        range=sheet_name
    ).execute()
    return response["values"]


def validate_data(data: dict):
    insert_data = [
        data['name'],
        data['id'],
    ]
    return insert_data


def write_to_google_sheet(data: dict, table_link: str, table_sheet_name: str):
    """
    Отправляем данные в гугл таблицу по указанному айди таблицы и названию листа
    """
    service = get_service()
    valid_data = validate_data(data)
    body = {
        "values": [valid_data]
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=table_link, range=f"{table_sheet_name}!1:{len(valid_data)}",
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
    update_sheet_name(response["sheetId"], sheet_name)




