from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.conf import settings


from ..services.skorozvon import skorozvon_api
from ..services.google_sheets import google_sheets_api
from .db_requests import (
    get_db_leads_count_for_interval,
    get_db_dialogs_count_for_interval,
    get_db_contacts_count_for_interval,
)

LOCAL_TZ = 3


def write_project_stat_to_google_sheet(sheet_name: str, projects_stat: dict, is_prev=False):
    """
    Функция записывает статистику по проектам за интервал в таблицу
    :param sheet_name: имя листа в гугл таблице, куда идет запись
    :param projects_stat: словарь, позволяющий получить статистику проекта по имени
    :param is_prev: флаг, определяющий записывать ли в диапазон текущих данных или диапазон прошлых данных
    """
    start_cell_letter = "AE" if is_prev else "A"
    google_sheets_api.write_to_google_sheet(
        [[sheet_name]],
        settings.GS_LEADS_TABLE_ID,
        sheet_name,
        f"{google_sheets_api.calc_cell_letter(start_cell_letter, 2)}1"
    )
    google_sheets_api.write_to_google_sheet(
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
    projects_indexes = get_project_indexes()
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
            elif project in projects_stat:
                result.append(projects_stat[project][column])
                project_total += result[-1]
            else:
                result.append(0)
        cell_num = field_table_shift[column]
        column_num = google_sheets_api.calc_cell_letter(start_cell_letter, cell_num)
        sheet_range = (f"{column_num}{google_sheets_api.START_CELL_NUM}:"
                       f"{column_num}{google_sheets_api.START_CELL_NUM + len(projects_indexes)}")
        google_sheets_api.write_to_google_sheet(
            [[value] for value in result],
            settings.GS_LEADS_TABLE_ID,
            sheet_name,
            sheet_range
        )


def get_date_from_sheet_name(sheet_name: str, index: int):
    """
    Функия получает дату из названия листа
    :param sheet_name: Название листа
    :param index: Индекс (1 или 0) в зависимости от того, нужно получить начальную или конечную дату
    :return: полученную дату в формате datetime
    """
    return datetime.strptime(sheet_name.split(" (")[0].split("-")[index], google_sheets_api.DATE_FORMAT_FOR_SHEET_NAME)


def get_project_indexes():
    """
    Функция забирает данные из таблицы, проходит по ячейкам с названиями, пока не дойдет до строки "ИТОГО ПО ВСЕМ"
    И далее формирует словарь, связывающий имя проекта и номер строки в таблице
    :return: Словарь с соответствием названия проекта номеру его строки в таблице
    """
    table = google_sheets_api.get_table_data(
        settings.GS_LEADS_TABLE_ID,
        settings.GS_LEADS_MAIN_SHEET_NAME,
        f"A{google_sheets_api.START_CELL_NUM}:B"
    )
    project_indexes = []
    for i, line in enumerate(table):
        project_indexes.append(
            line[0] if "ИТОГО" in line[0] else settings.GS_TO_SKOROZVON_PROJECT_NAME.get(line[1], "")
        )
        if len(line) == 1 and line[0] == "ИТОГО ПО ВСЕМ:":
            break
    return project_indexes


def get_prev_sheet_name(current_sheet_name: str):
    """
    Функция получает название предыдущего листа,
    чья конечная дата наиболее приближена к начальной дате текущего листа
    :param current_sheet_name: Имя текущего листа
    :return: Название предыдущего листа
    """
    start_date = get_date_from_sheet_name(current_sheet_name, 0)
    sheet_names = google_sheets_api.get_sheet_names(settings.GS_LEADS_TABLE_ID)
    validated_sheet_names = list(filter(lambda sheet_name: "-" in sheet_name, sheet_names))
    prev_sheet_name = min(validated_sheet_names, key=lambda sheet_name: abs(
        start_date - get_date_from_sheet_name(sheet_name, 1)
    ))
    return prev_sheet_name


def write_prev_data_to_google_sheet(sheet_name: str, prev_sheet_name: str):
    """
    Гугл-таблица состоит из двух таблиц - данные за текущий интервал, и данные за прошлый интервал.
    Функция берет данные из прошлой таблцы "текущий интервал" и заносит их в новую таблицу в "прошлый интервал"
    :param sheet_name: Имя текущего листа
    :param prev_sheet_name: Имя прошлого листа
    :return:
    """
    previous_table_data = google_sheets_api.get_table_data(
        settings.GS_LEADS_TABLE_ID,
        prev_sheet_name,
        google_sheets_api.MAIN_TABLE_RANGE
    )
    google_sheets_api.write_to_google_sheet(
        previous_table_data,
        settings.GS_LEADS_TABLE_ID,
        sheet_name,
        google_sheets_api.PREV_TABLE_RANGE
    )


def str_form_unix(unix_time: int):
    """
    конвертирует время в формате unix в строку
    """
    return datetime.utcfromtimestamp(unix_time).strftime(google_sheets_api.DATE_FORMAT_FOR_SHEET_NAME)


def create_report_sheet(sheet_name, prev_sheet_name):
    """
    создает новый лист на основе шаблона и заносит данные из прошлого диапазона
    :param sheet_name: имя листа
    :param prev_sheet_name: имя листа за прошлый интервал
    """
    sheet_id = google_sheets_api.create_sheet_copy(
        settings.GS_LEADS_TABLE_ID,
        settings.GS_LEADS_MAIN_SHEET_ID,
    )
    google_sheets_api.update_sheet_property(settings.GS_LEADS_TABLE_ID, sheet_id, "title", sheet_name)
    google_sheets_api.update_sheet_property(settings.GS_LEADS_TABLE_ID, sheet_id, "index", "0")
    write_prev_data_to_google_sheet(sheet_name, prev_sheet_name)


def create_report(projects_stat: dict, start_date: int, end_date: int, prev_start_date: int):
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
    sheet_name = f"{str_form_unix(start_date)}-{str_form_unix(end_date)}"
    prev_sheet_name = f"{str_form_unix(prev_start_date)}-{str_form_unix(start_date)}"
    if sheet_name not in google_sheets_api.get_sheet_names(settings.GS_LEADS_TABLE_ID):
        create_report_sheet(sheet_name, prev_sheet_name)
    write_project_stat_to_google_sheet(
        sheet_name=sheet_name,
        projects_stat=projects_stat,
    )


def write_updated_dialog_statistics(start_date, end_date, prev_start_date):
    """
    Собирает статистику по проектам за выбранный интервал и создает отчет
    """
    project_ids = skorozvon_api.get_projects_ids()
    scenario_ids = skorozvon_api.get_projects_ids()
    if not project_ids:
        return
    projects_stat = dict()
    filters = {
        "start_date": start_date,
        "end_date": end_date,
    }
    for project_name, project_id in project_ids.items():
        # TODO: get scenario_id from project_id
        scenario_name = settings.SKOROZVON_PROJECT_TO_SKOROZVON_SCENARIO_NAME.get(project_name, "")
        scenario_id = scenario_ids.get(scenario_name, "")
        projects_stat[project_name] = {
            "contacts": get_db_contacts_count_for_interval(**filters, project_id=project_id),
            "dialogs": get_db_dialogs_count_for_interval(**filters, scenario_id=scenario_id),
            "leads": get_db_leads_count_for_interval(**filters, scenario_id=scenario_id),
        }
    create_report(projects_stat, start_date, end_date, prev_start_date)


def update_two_weeks_dialog_statistics():
    """
    Создает двухнедельный отчет о контактах, диалогах и лидах
    """
    today = datetime.today().replace(hour=LOCAL_TZ, minute=0, second=0, microsecond=0)
    if today.day > 15:
        two_weeks_ago = today.replace(day=16)
        today = (today + relativedelta(months=1)).replace(day=1)
    else:
        two_weeks_ago = today.replace(day=1)
        today = today.replace(day=16)
    start_date = datetime.timestamp(two_weeks_ago)
    end_date = datetime.timestamp(today)
    prev_start_date = datetime.timestamp(today - relativedelta(months=1))
    write_updated_dialog_statistics(start_date, end_date, prev_start_date)


def update_month_dialog_statistics():
    """
    Создает месячный отчет о контактах, диалогах и лидах
    """
    today = datetime.today().replace(day=1, hour=LOCAL_TZ, minute=0, second=0, microsecond=0)
    start_date = datetime.timestamp(today)
    end_date = datetime.timestamp(today + relativedelta(months=1))
    prev_start_date = datetime.timestamp(today - relativedelta(months=1))
    write_updated_dialog_statistics(start_date, end_date, prev_start_date)
