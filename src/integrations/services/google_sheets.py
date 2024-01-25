from datetime import datetime, timedelta
import os

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from django.conf import settings


class GoogleSheetsApi:
    MAIN_TABLE_RANGE = "A:AC"
    PREV_TABLE_RANGE = "AE1:BG54"
    DATE_FORMAT_FOR_SHEET_NAME = '%d.%m.%y'
    _service = None

    def __init__(self):
        self._service = self.get_service()

    def get_service(self):
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

    def get_project_indexes(self):
        """
        Функция забирает данные из таблицы, проходит по ячейкам с названиями, пока не дойдет до строки "ИТОГО ПО ВСЕМ"
        И далее формирует словарь, связывающий имя проекта и номер строки в таблице
        :return: Словарь с соответствием названия проекта номеру его строки в таблице
        """
        start_index = 8
        table = self.get_table_data(
            settings.GS_TABLE_ID,
            settings.GS_MAIN_SHEET_NAME,
            f"A{start_index}:B"
        )
        project_indexes = dict()
        for i, line in enumerate(table):
            if len(line) == 1 and line[0] == "ИТОГО ПО ВСЕМ:":
                break
            if len(line) == 2:
                project_indexes[line[1]] = i + start_index
        return project_indexes

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
                return f"A{chr(ord(new_letter)-26)}"
            else:
                return f"{chr(ord(start_cell[0])+1)}{chr(ord(new_letter)-26)}"
        else:
            return f"{start_cell[:-1]}{new_letter}"

    def get_data_diapason(self, week: int):
        return (f"{(datetime.utcnow() - timedelta(weeks=week + 2)).strftime(self.DATE_FORMAT_FOR_SHEET_NAME)}-"
                f"{(datetime.utcnow() - timedelta(weeks=week)).strftime(self.DATE_FORMAT_FOR_SHEET_NAME)}")

    def write_project_stat_to_google_sheet(self, sheet_name: str, projects_stat: dict, is_prev=False):
        """
        Функция записывает статистику по проектам за интервал в таблицу
        :param sheet_name: имя листа в гугл таблице, куда идет запись
        :param projects_stat: словарь, позволяющий получить статистику проекта по имени
        :param is_prev: флаг, определяющий записывать ли в диапазон текущих данных или диапазон прошлых данных
        """
        start_cell_letter = "AE" if is_prev else "A"
        self.write_to_google_sheet(
            [[sheet_name]],
            settings.GS_TABLE_ID,
            sheet_name,
            f"{self.calc_cell_letter(start_cell_letter, 2)}1"
        )
        self.write_to_google_sheet(
            [[sheet_name]],
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
        projects_indexes = self.get_project_indexes()
        for project_name, project_stat in projects_stat.items():
            cell_num = projects_indexes[settings.SKOROZVON_PROJECT_TO_GS_NAME[project_name]]
            for field_name, shift in field_table_shift.items():
                self.write_to_google_sheet(
                    [[project_stat[field_name]]],
                    settings.GS_TABLE_ID,
                    sheet_name,
                    f"{self.calc_cell_letter(start_cell_letter, shift)}{cell_num}"
                )

    def get_date_from_sheet_name(self, sheet_name: str, index: int):
        """
        Функия получает дату из названия листа
        :param sheet_name: Название листа
        :param index: Индекс (1 или 0) в зависимости от того, нужно получить начальную или конечную дату
        :return: полученную дату в формате datetime
        """
        return datetime.strptime(sheet_name.split(" (")[0].split("-")[index], self.DATE_FORMAT_FOR_SHEET_NAME)

    def get_prev_sheet_name(self, current_sheet_name: str):
        """
        Функция получает название предыдущего листа,
        чья конечная дата наиболее приближена к начальной дате текущего листа
        :param current_sheet_name: Имя текущего листа
        :return: Название предыдущего листа
        """
        start_date = self.get_date_from_sheet_name(current_sheet_name, 0)
        sheet_names = self.get_sheet_names()
        validated_sheet_names = list(filter(lambda sheet_name: "-" in sheet_name, sheet_names))
        prev_sheet_name = min(validated_sheet_names, key=lambda sheet_name: abs(
            start_date - self.get_date_from_sheet_name(sheet_name, 1)
        ))
        return prev_sheet_name

    def write_prev_data_to_google_sheet(self, sheet_name: str, prev_sheet_name: str):
        """
        Гугл-таблица состоит из двух таблиц - данные за текущий интервал, и данные за прошлый интервал.
        Функция берет данные из прошлой таблцы "текущий интервал" и заносит их в новую таблицу в "прошлый интервал"
        :param sheet_name: Имя текущего листа
        :param prev_sheet_name: Имя прошлого листа
        :return:
        """
        previous_table_data = self.get_table_data(settings.GS_TABLE_ID, prev_sheet_name, self.MAIN_TABLE_RANGE)
        self.write_to_google_sheet(previous_table_data, settings.GS_TABLE_ID, sheet_name, self.PREV_TABLE_RANGE)

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

    def update_sheet_property(self, sheet_id: int, field_name: str, field_value: str):
        """
        Функция изменяет характеристику листа
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
        self._service.spreadsheets().batchUpdate(spreadsheetId=settings.GS_TABLE_ID, body=body).execute()

    def get_sheet_names(self):
        """
        Функция возвращает имена листов в таблице
        :return: Список имен
        """
        sheet_metadata = self._service.spreadsheets().get(spreadsheetId=settings.GS_TABLE_ID).execute()
        sheets = sheet_metadata.get('sheets', '')
        return [sheet.get("properties", {}).get("title", "") for sheet in sheets]

    def create_sheet_name(self, sheet_name):
        """
        Функция провреяет лист на дубли, и если лист с таким название существует - возвращает <имя (номер копии)>
        :param sheet_name: имя листа
        :return: Имя листа
        """
        sheet_names = self.get_sheet_names()
        postfix = 0
        while True:
            if sheet_name in sheet_names:
                postfix += 1
                sheet_name = f"{sheet_name.split(' (')[0]} ({postfix})"
            else:
                return sheet_name

    def str_form_unix(self, unix_time: int):
        return datetime.utcfromtimestamp(unix_time).strftime(self.DATE_FORMAT_FOR_SHEET_NAME)

    def create_report_sheet(self, projects_stat: dict, start_date: int, end_date: int, prev_start_date: int):
        """
        Функция формирует отчет по статистике в таблицу.
        Создается копия листа-шаблона, переименовывается и устанавливается первым при отображении в таблице
        Далее в данный лист записываются актуальные данные и данные из прошлой таблицы для сравнения
        :param projects_stat: словарь, позволяющий получить статистику проекта по имени
        """
        sheet_name = self.create_sheet_name(
            f"{self.str_form_unix(start_date)}-{self.str_form_unix(end_date)}"
        )
        prev_sheet_name = self.create_sheet_name(
            f"{self.str_form_unix(prev_start_date)}-{self.str_form_unix(start_date)}"
        )
        sheet_id = self.create_sheet_copy(
            settings.GS_TABLE_ID,
            settings.GS_MAIN_SHEET_ID,
        )
        self.update_sheet_property(sheet_id, "title", sheet_name)
        self.update_sheet_property(sheet_id, "index", "0")
        self.write_project_stat_to_google_sheet(
            sheet_name=sheet_name,
            projects_stat=projects_stat,

        )
        self.write_prev_data_to_google_sheet(sheet_name, prev_sheet_name)


google_sheets_api = GoogleSheetsApi()
