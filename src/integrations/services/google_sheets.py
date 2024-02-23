import os

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from django.conf import settings


class GoogleSheetsApi:
    START_CELL_NUM = 8
    MAIN_TABLE_RANGE = "A:AC"
    PREV_TABLE_RANGE = "AE1:BG54"
    DATE_FORMAT_FOR_SHEET_NAME = '%d.%m.%y'
    KPI_TABLE_START_CELL_NUM = 4
    KPI_TABLE_FINISH_CELL_NUM = 34
    MONTH_FROM_NUM = {
        1: 'Январь',
        2: 'Февраль',
        3: 'Март',
        4: 'Апрель',
        5: 'Май',
        6: 'Июнь',
        7: 'июль',
        8: 'Август',
        9: 'Сентябрь',
        10: 'Октябрь',
        11: 'Ноябрь',
        12: 'Декабрь'
    }
    _service = None

    def __init__(self):
        self._service = self.get_service()

    @staticmethod
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

    def get_table_data(self, table_link, sheet_name, sheet_range):
        """
        Функция получает данные из указанной таблицы с указанного листа в указанном дапазоне
        :param table_link: Адрес гугл таблицы
        :param sheet_name: Адрес листа
        :param sheet_range: Диапазон ячеек
        :return: Значения из таблицы
        """
        search_range = sheet_name
        if sheet_range:
            search_range = f"{sheet_name}!{sheet_range}"
        response = self._service.spreadsheets().values().get(
            spreadsheetId=table_link,
            range=search_range
        ).execute()
        return response["values"]

    def write_to_google_sheet(self, data: list[list], table_link: str, table_sheet_name: str, sheet_range: str):
        """
        Функция записывает информацию в гугл-таблицу
        :param data: Список из списков с информацией по столбцам
        :param table_link: Адрес таблицы
        :param table_sheet_name: Имя листа таблицы
        :param sheet_range: диапазон ячеек или ячейка для записи
        """
        body = {
            "values": data
        }
        self._service.spreadsheets().values().update(
            spreadsheetId=table_link, range=f"{table_sheet_name}!{sheet_range}",
            valueInputOption="USER_ENTERED", body=body
        ).execute()

    @staticmethod
    def calc_cell_letter(start_cell: str, shift: int):
        """
        Функция рассчитывает адрес колонки, полученной путем сдвига на указанное число столбцов
        С учетом, что после Z идет колонка AA, а после AZ - BA
        :param start_cell: Буква, с которой начинается отсчет по столбцам
        :param shift: Число столбцов, на которые необходимо сдвинуться
        :return: Адрес полученной колонки
        """
        new_letter = chr(ord(start_cell[-1]) + shift)
        if new_letter > "Z":
            if len(start_cell) == 1:
                return f"A{chr(ord(new_letter) - 26)}"
            else:
                return f"{chr(ord(start_cell[0]) + 1)}{chr(ord(new_letter) - 26)}"
        else:
            return f"{start_cell[:-1]}{new_letter}"

    def create_sheet_copy(self, copy_table_id: str, copy_sheet_id: int):
        """
        Функция создает копию листа в этой же таблице
        :param copy_table_id: идентификатор копируемого листа
        :param copy_sheet_id: идентификатор таблицы
        :return: идентификатор созданного листа
        """
        body = {
            "destinationSpreadsheetId": copy_table_id,
        }
        response = self._service.spreadsheets().sheets().copyTo(
            spreadsheetId=copy_table_id,
            sheetId=copy_sheet_id,
            body=body,
        ).execute()
        return response["sheetId"]

    def update_sheet_property(self, table_id: str, sheet_id: int, field_name: str, field_value: str):
        """
        Функция изменяет характеристику листа
        :param table_id: идентификатор таблицы
        :param sheet_id: идентификатор листа
        :param field_name: имя изменяемого поля
        :param field_value: значение изменяемого поля
        """
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
        self._service.spreadsheets().batchUpdate(spreadsheetId=table_id, body=body).execute()

    def get_sheet_meta(self, table_id):
        """
        Функция возвращает данные о листах в таблице
        :return: данные о листах в таблице
        """
        sheet_metadata = self._service.spreadsheets().get(spreadsheetId=table_id).execute()
        sheets = sheet_metadata.get('sheets', '')
        return [sheet.get("properties", {}) for sheet in sheets]

    def get_sheet_names(self, table_id):
        """
        Функция возвращает имена листов в таблице
        :return: Список имен
        """
        return [sheet.get("title", "") for sheet in self.get_sheet_meta(table_id)]

    def get_sheet_id_by_name(self, table_id, sheet_name):
        for sheet in self.get_sheet_meta(table_id):
            if sheet.get("title", "") == sheet_name:
                return sheet.get("sheetId", "")
        return ""

    @staticmethod
    def get_merge_data(sheet_id, start_row, end_row, start_col, end_col):
        """
        Функция возвращает тело запроса на слияние ячеек.
        """
        return {
            "mergeCells": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_row,
                    "endRowIndex": end_row,
                    "startColumnIndex": start_col,
                    "endColumnIndex": end_col
                },
                "mergeType": "MERGE_ALL"
            }
        },

    def merge_cells(self, table_id, merge_data):
        """
        Отправляет запрос на слияние ячеек, указанных в параметрах
        :param table_id: id таблицы
        :param merge_data: список тел запроса для слияния (тела берутся из get_merge_data)
        """
        return self._service.spreadsheets().batchUpdate(
            spreadsheetId=table_id,
            body={"requests": merge_data}
        ).execute()

    def add_borders(self, table_id, sheet_id, start_row, end_row, start_col, end_col):
        """
        Выделяет таблицу рамками в указанных координатах
        """
        sides = ["top", "bottom", "left", "right", "innerHorizontal", "innerVertical"]
        body = {
            "requests": [
                {
                    "updateBorders": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": start_row,
                            "endRowIndex": end_row,
                            "startColumnIndex": start_col,
                            "endColumnIndex": end_col
                        },
                    }
                }
            ]
        }
        for side in sides:
            body["requests"][0]["updateBorders"][side] = {
                "style": "SOLID",
                "width": 1,
            }
        return self._service.spreadsheets().batchUpdate(
            spreadsheetId=table_id,
            body=body
        ).execute()

    def create_sheet(self, sheet_name, table_id):
        """
        создает новый лист в таблице
        :return ID создаенного листа
        """
        body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name,
                    }
                }
            }]
        }
        response = self._service.spreadsheets().batchUpdate(
            spreadsheetId=table_id,
            body=body
        ).execute()
        return response["replies"][0]["addSheet"]["properties"]["sheetId"]


google_sheets_api = GoogleSheetsApi()
