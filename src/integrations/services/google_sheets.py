import calendar
from datetime import datetime, timedelta, date
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
        table = self.get_table_data(
            settings.GS_LEADS_TABLE_ID,
            settings.GS_LEADS_MAIN_SHEET_NAME,
            f"A{self.START_CELL_NUM}:B"
        )
        project_indexes = []
        for i, line in enumerate(table):
            project_indexes.append(
                line[0] if "ИТОГО" in line[0] else settings.GS_TO_SKOROZVON_PROJECT_NAME.get(line[1], "")
            )
            if len(line) == 1 and line[0] == "ИТОГО ПО ВСЕМ:":
                break
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
                return f"A{chr(ord(new_letter) - 26)}"
            else:
                return f"{chr(ord(start_cell[0]) + 1)}{chr(ord(new_letter) - 26)}"
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
            settings.GS_LEADS_TABLE_ID,
            sheet_name,
            f"{self.calc_cell_letter(start_cell_letter, 2)}1"
        )
        self.write_to_google_sheet(
            [[sheet_name]],
            settings.GS_LEADS_TABLE_ID,
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
        for column in ["contacts", "dialogs", "leads"]:
            result = []
            total = 0
            project_total = 0
            for i, project in enumerate(projects_indexes):
                if project == "":
                    result.append(0)
                elif project == "ИТОГО:":
                    result.append(project_total)
                    total += project_total
                    project_total = 0
                elif project == "ИТОГО ПО ВСЕМ:":
                    result.append(total)
                else:
                    result.append(projects_stat[project][column])
                    project_total += result[-1]
            cell_num = field_table_shift[column]
            sheet_range = (f"{self.calc_cell_letter(start_cell_letter, cell_num)}{self.START_CELL_NUM}:"
                           f"{self.calc_cell_letter(start_cell_letter, cell_num)}{self.START_CELL_NUM + len(projects_indexes)}")
            self.write_to_google_sheet(
                [[value] for value in result],
                settings.GS_LEADS_TABLE_ID,
                sheet_name,
                sheet_range
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
        sheet_names = self.get_sheet_names(settings.GS_LEADS_TABLE_ID)
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
        previous_table_data = self.get_table_data(settings.GS_LEADS_TABLE_ID, prev_sheet_name, self.MAIN_TABLE_RANGE)
        self.write_to_google_sheet(previous_table_data, settings.GS_LEADS_TABLE_ID, sheet_name, self.PREV_TABLE_RANGE)

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

    def get_sheet_names(self, table_id):
        """
        Функция возвращает имена листов в таблице
        :return: Список имен
        """
        sheet_metadata = self._service.spreadsheets().get(spreadsheetId=table_id).execute()
        sheets = sheet_metadata.get('sheets', '')
        return [sheet.get("properties", {}).get("title", "") for sheet in sheets]

    def str_form_unix(self, unix_time: int):
        return datetime.utcfromtimestamp(unix_time).strftime(self.DATE_FORMAT_FOR_SHEET_NAME)

    def create_report_sheet(self, sheet_name, prev_sheet_name):
        sheet_id = self.create_sheet_copy(
            settings.GS_LEADS_TABLE_ID,
            settings.GS_LEADS_MAIN_SHEET_ID,
        )
        self.update_sheet_property(settings.GS_LEADS_TABLE_ID, sheet_id, "title", sheet_name)
        self.update_sheet_property(settings.GS_LEADS_TABLE_ID, sheet_id, "index", "0")
        self.write_prev_data_to_google_sheet(sheet_name, prev_sheet_name)

    def create_report(self, projects_stat: dict, start_date: int, end_date: int, prev_start_date: int):
        """
        Функция формирует отчет по статистике в таблицу.
        Создается копия листа-шаблона, переименовывается и устанавливается первым при отображении в таблице
        Далее в данный лист записываются актуальные данные и данные из прошлой таблицы для сравнения
        :param projects_stat: соответствие имени проекта и его статистики
        :param start_date: дата начала текущего интервала
        :param end_date: дата конца текущего интервала
        :param prev_start_date: дата начала прошлого интервала
        :return:
        """
        sheet_name = f"{self.str_form_unix(start_date)}-{self.str_form_unix(end_date)}"
        prev_sheet_name = f"{self.str_form_unix(prev_start_date)}-{self.str_form_unix(start_date)}"
        if sheet_name not in self.get_sheet_names(settings.GS_LEADS_TABLE_ID):
            self.create_report_sheet(sheet_name, prev_sheet_name)
        self.write_project_stat_to_google_sheet(
            sheet_name=sheet_name,
            projects_stat=projects_stat,

        )

    def get_kpi_user_cells(self, sheet_name):
        names_row = self.get_table_data(settings.GS_KPI_TABLE_ID, sheet_name, "")[0]
        return {
            user_name: self.calc_cell_letter("A", i)
            for i, user_name in enumerate(names_row)
            if user_name and user_name != "Дата"
        }

    def get_current_sheet_name(self):
        return f"{self.MONTH_FROM_NUM[int(datetime.now().strftime('%m'))]} {datetime.now().strftime('%Y')[-2:]}"

    @staticmethod
    def get_current_month_days_amount():
        month, year = int(datetime.now().strftime('%m')), int(datetime.now().strftime('%Y'))
        return calendar.monthrange(year, month)[1]

    def write_dates_column(self, sheet_name: str):
        self.write_to_google_sheet(
            [["Дата"]],
            settings.GS_KPI_TABLE_ID,
            sheet_name,
            f"A1:A{self.KPI_TABLE_START_CELL_NUM - 1}"
        )
        month, year = int(datetime.now().strftime('%m')), int(datetime.now().strftime('%Y'))
        num_days = calendar.monthrange(year, month)[1]
        days = [[date(year, month, day).strftime("%Y-%m-%d")] for day in range(1, num_days + 1)]
        days.append(["Итого"])
        days.append([])
        days.append(["Премии"])
        self.write_to_google_sheet(
            days,
            settings.GS_KPI_TABLE_ID,
            sheet_name,
            f"A{self.KPI_TABLE_START_CELL_NUM}:A{len(days) + self.KPI_TABLE_START_CELL_NUM}"
        )

    def get_cell_num_by_date(self, sheet_name):
        current_date = datetime.now().strftime("%Y-%m-%d")
        return self.get_table_data(
            settings.GS_KPI_TABLE_ID,
            sheet_name,
            f"A{self.KPI_TABLE_START_CELL_NUM}:A{self.KPI_TABLE_FINISH_CELL_NUM}"
        ).index([current_date]) + self.KPI_TABLE_START_CELL_NUM

    def get_kpi_users_list(self):
        return [user[0] for user in self.get_table_data(
            settings.GS_KPI_TABLE_ID,
            settings.GS_KPI_USERS_SHEET_NAME,
            f"A:A"
        )[1:] if user]

    @staticmethod
    def get_merge_data(sheet_id, start_row, end_row, start_col, end_col):
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
        return self._service.spreadsheets().batchUpdate(
            spreadsheetId=table_id,
            body={"requests": merge_data}
        ).execute()

    def add_kpi_column(self, sheet_name, user_name, index, days_amount):
        data = self.get_table_data(
            settings.GS_KPI_TABLE_ID,
            settings.GS_KPI_USERS_SHEET_TEMPLATE_NAME,
            "B1:E6"
        )
        data[0].append(user_name)
        start_letter = self.calc_cell_letter('B', index * 4)
        for i in range(len(data[-3])):
            current_letter = self.calc_cell_letter(start_letter, i)
            data[-2][i] = (f'=СУММ({current_letter}{self.KPI_TABLE_START_CELL_NUM}'
                           f':{current_letter}{self.KPI_TABLE_START_CELL_NUM+days_amount - 1})')
        for i in range(2):
            current_letter = self.calc_cell_letter(start_letter, i * 2 + 1)
            data[-1][i * 2 + 1] = (
                f'={current_letter}{self.KPI_TABLE_START_CELL_NUM + days_amount}-'
                f'{self.calc_cell_letter(current_letter, -1)}{self.KPI_TABLE_START_CELL_NUM + days_amount}'
            )
        data[-1][2] = (
                f'={self.calc_cell_letter(start_letter, 3)}{self.KPI_TABLE_START_CELL_NUM + days_amount + 1}/'
                f'{self.calc_cell_letter(start_letter, 1)}{self.KPI_TABLE_START_CELL_NUM + days_amount + 1}'
        )
        for day in range(days_amount):
            data.insert(3, [])
        self.write_to_google_sheet(
            data,
            settings.GS_KPI_TABLE_ID,
            sheet_name,
            f"{start_letter}:{self.calc_cell_letter(start_letter, 3)}"
        )

    def append_kpi_new_user(self, user_name, index):
        sheet_name = self.get_current_sheet_name()
        days_amount = self.get_current_month_days_amount()
        self.add_kpi_column(sheet_name, user_name, index, days_amount)

    def add_borders(self, table_id, sheet_id, start_row, end_row, start_col, end_col):
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

    def add_total_table(self, sheet_name, days_amount, users_amount):
        start_num = 10
        block_size = 19
        data = self.get_table_data(
            settings.GS_KPI_TABLE_ID,
            settings.GS_KPI_USERS_SHEET_TEMPLATE_NAME,
            f"A{start_num}:E{start_num + 19}"
        )
        # Plan
        plan_sum_formula = '+'.join(
            f"{self.calc_cell_letter('B', i * 4)}{days_amount+4}" for i in range(users_amount)
        )
        data[9][1] = f"={plan_sum_formula}"
        # Fact
        fact_sum_formula = '+'.join(
            f"{self.calc_cell_letter('C', i * 4)}{days_amount + 4}" for i in range(users_amount)
        )
        data[10][1] = f"={fact_sum_formula}"
        data[10][2] = f"=B{start_num + days_amount + 9}-B{start_num + days_amount + 10}"
        self.write_to_google_sheet(
            data,
            settings.GS_KPI_TABLE_ID,
            sheet_name,
            f"A{start_num + days_amount}:E{start_num + block_size + days_amount}"
        )

    def crate_kpi_sheet(self, users, sheet_name):
        sheet_id = self.create_sheet(
            table_id=settings.GS_KPI_TABLE_ID,
            sheet_name=sheet_name
        )
        self.update_sheet_property(settings.GS_KPI_TABLE_ID, sheet_id, "index", "0")
        merge_data = []
        days_amount = self.get_current_month_days_amount()
        # merge data field
        merge_data.append(
            self.get_merge_data(sheet_id, 0, 3, 0, 1)
        )
        for i, user in enumerate(users):
            self.add_kpi_column(sheet_name, user, i, days_amount)
            # merge name
            merge_data.append(
                self.get_merge_data(sheet_id, 0, 1, i * 4 + 1, i * 4 + 5)
            )
            # merge out calls
            merge_data.append(
                self.get_merge_data(sheet_id, 1, 2, i * 4 + 1, i * 4 + 3)
            )
            # merge leads
            merge_data.append(
                self.get_merge_data(sheet_id, 1, 2, i * 4 + 3, i * 4 + 5)
            )
        self.merge_cells(settings.GS_KPI_TABLE_ID, merge_data)
        self.add_borders(settings.GS_KPI_TABLE_ID, sheet_id, 0, days_amount + 6, 0, len(users) * 4 + 1)
        self.add_total_table(sheet_name, days_amount, len(users))

    def create_sheet(self, sheet_name, table_id):
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

    def create_kpi_report(self, users_stat: dict):
        sheet_name = self.get_current_sheet_name()
        if sheet_name not in self.get_sheet_names(settings.GS_KPI_TABLE_ID):
            self.crate_kpi_sheet(users_stat.keys(), sheet_name)
        cell_num = self.get_cell_num_by_date(sheet_name)
        for user, column_name in self.get_kpi_user_cells(sheet_name).items():
            field_shifts = {"dialogs": 1, "leads": 3}
            for field, shift in field_shifts.items():
                cell_address = f"{self.calc_cell_letter(column_name, shift)}{cell_num}"
                self.write_to_google_sheet(
                    [[users_stat[user][field]]],
                    settings.GS_KPI_TABLE_ID,
                    sheet_name,
                    cell_address
                )


google_sheets_api = GoogleSheetsApi()
