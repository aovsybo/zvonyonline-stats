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


def write_to_google_sheet(data: str, table_link: str, table_sheet_name: str, sheet_range: str):
    """
    Отправляем данные в гугл таблицу по указанному айди таблицы и названию листа
    """
    service = get_service()
    body = {
        "values": data
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=table_link, range=f"{table_sheet_name}!{sheet_range}",
        valueInputOption="USER_ENTERED", body=body).execute()
    return result


def write_to_cell_google_sheet(data: str, table_link: str, table_sheet_name: str, cell_id: str):
    """
    Отправляем данные в гугл таблицу по указанному айди таблицы и названию листа
    """
    service = get_service()
    body = {
        "values": [[data]]
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=table_link, range=f"{table_sheet_name}!{cell_id}",
        valueInputOption="USER_ENTERED", body=body).execute()
    return result


def calc_cell_letter(start_cell: str, shift: int):
    new_letter = chr(ord(start_cell[-1]) + shift)
    if new_letter > "z":
        if len(start_cell) == 1:
            return f"A{chr(ord(new_letter)-26)}"
        else:
            return f"{chr(ord(start_cell[0])+1)}{chr(ord(new_letter)-26)}"
    else:
        return f"{start_cell[:-1]}{new_letter}"


def write_project_stat_to_google_sheet(sheet_name: str, projects_stat: dict, projects_indexes: dict, is_prev=False):
    start_cell_letter = "AE" if is_prev else "A"
    write_to_cell_google_sheet(
        sheet_name,
        settings.GS_TABLE_ID,
        sheet_name,
        f"{calc_cell_letter(start_cell_letter, 2)}1"
    )
    write_to_cell_google_sheet(
        sheet_name,
        settings.GS_TABLE_ID,
        sheet_name,
        f"{start_cell_letter}32"
    )
    # Соответствие названия поля, куда мы вписываем значение, с его сдвигом от start_cell_letter
    field_table_shift = {
        "contacts": 2,
        "dialogs": 5,
        "leads": 9,
    }
    for project_name, project_stat in projects_stat.items():
        cell_num = projects_indexes[settings.SKOROZVON_PROJECT_TO_GS_NAME[project_name]]
        for field_name, shift in field_table_shift.items():
            write_to_cell_google_sheet(
                project_stat[field_name],
                settings.GS_TABLE_ID,
                sheet_name,
                f"{calc_cell_letter(start_cell_letter, shift)}{cell_num}"
            )


def write_prev_data_to_google_sheet(sheet_name: str, prev_sheet_name: str):
    prev_table = get_table_data(settings.GS_TABLE_ID, prev_sheet_name, "A:AC")
    write_to_google_sheet(prev_table, settings.GS_TABLE_ID, sheet_name, "AE1:BG54")


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


def update_sheet_property(sheet_id: int, field_name: str, field_value: str):
    service = get_service()
    body = {
        'requests':
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    field_name: field_value,
                },
                "fields": field_name,
            }
        }
    }
    return service.spreadsheets().batchUpdate(spreadsheetId=settings.GS_TABLE_ID, body=body).execute()


def create_main_sheet_copy(sheet_name: str):
    response = create_sheet_copy(
        settings.GS_TABLE_ID,
        settings.GS_MAIN_SHEET_ID,
    )
    update_sheet_property(response["sheetId"], "title", sheet_name)
    update_sheet_property(response["sheetId"], "index", "0")
    return response["sheetId"]


def get_sz_to_gs_data():
    return {
        scenario[0]: scenario[1]
        for scenario in get_table_data(
            settings.GS_TABLE_ID,
            "Соответствия",
            "B:C"
        )[1:]
        if scenario[0] != "-"
    }
