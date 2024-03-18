import calendar
from datetime import datetime, date

from django.conf import settings

from ..api.serializers import UsersKPISerializer
from .db_requests import get_user_stat, remove_inactive_users
from ..models import UsersKPI
from ..services.skorozvon import skorozvon_api
from ..services.google_sheets import google_sheets_api


def add_total_table(sheet_name, days_amount, users_amount):
    """
    Добавляет в таблицу суммарную статистику по всем сотрудникам
    :param sheet_name: имя листа
    :param days_amount: количество дней в месяце (для расчета номера строки куда вставлять табличку)
    :param users_amount: количество сотрудников (для расчета количества ячеек, которые необходимо подставлять в формулу)
    """
    start_num = 10
    block_size = 19
    data = google_sheets_api.get_table_data(
        settings.GS_KPI_TABLE_ID,
        settings.GS_KPI_USERS_SHEET_TEMPLATE_NAME,
        f"A{start_num}:E{start_num + 19}"
    )
    # Plan
    plan_sum_formula = '+'.join(
        f"{google_sheets_api.calc_cell_letter('B', i * 4)}{days_amount + 4}" for i in range(users_amount)
    )
    data[9][1] = f"={plan_sum_formula}"
    # Fact
    fact_sum_formula = '+'.join(
        f"{google_sheets_api.calc_cell_letter('C', i * 4)}{days_amount + 4}" for i in range(users_amount)
    )
    data[10][1] = f"={fact_sum_formula}"
    data[10][2] = f"=B{start_num + days_amount + 9}-B{start_num + days_amount + 10}"
    google_sheets_api.write_to_google_sheet(
        data,
        settings.GS_KPI_TABLE_ID,
        sheet_name,
        f"A{start_num + days_amount}:E{start_num + block_size + days_amount}"
    )


def create_kpi_sheet(users, sheet_name):
    """
    Создает лист с таблицей KPI. Размер таблицы пропорционален количеству сотрудников.
    У таблицы устанавливаются границы в виде рамок, а также происходит слияние некоторых ячеек
    :param users: список имен сотрудников
    :param sheet_name: имя создаваемого листа
    """
    sheet_id = google_sheets_api.create_sheet(
        table_id=settings.GS_KPI_TABLE_ID,
        sheet_name=sheet_name
    )
    google_sheets_api.update_sheet_property(settings.GS_KPI_TABLE_ID, sheet_id, "index", "0")
    write_dates_column(sheet_name)
    merge_data = []
    days_amount = get_current_month_days_amount()
    # merge data field
    merge_data.append(
        google_sheets_api.get_merge_data(sheet_id, 0, 3, 0, 1)
    )
    for i, user in enumerate(users):
        add_kpi_column(sheet_name, user, i, days_amount)
        # merge name
        merge_data.append(
            google_sheets_api.get_merge_data(sheet_id, 0, 1, i * 4 + 1, i * 4 + 5)
        )
        # merge out calls
        merge_data.append(
            google_sheets_api.get_merge_data(sheet_id, 1, 2, i * 4 + 1, i * 4 + 3)
        )
        # merge leads
        merge_data.append(
            google_sheets_api.get_merge_data(sheet_id, 1, 2, i * 4 + 3, i * 4 + 5)
        )
        # merge premium
        merge_data.append(
            google_sheets_api.get_merge_data(
                sheet_id,
                google_sheets_api.KPI_TABLE_START_CELL_NUM + days_amount + 1,
                google_sheets_api.KPI_TABLE_START_CELL_NUM + days_amount + 2,
                i * 4 + 1,
                i * 4 + 5
            )
        )
    google_sheets_api.merge_cells(settings.GS_KPI_TABLE_ID, merge_data)
    google_sheets_api.add_borders(settings.GS_KPI_TABLE_ID, sheet_id, 0, days_amount + 6, 0, len(users) * 4 + 1)
    add_total_table(sheet_name, days_amount, len(users))


def get_kpi_user_cells(sheet_name):
    """
    :return словарь с соответствием имени сотрудника и буквы, обозначающей его начальную колонку в таблице
    """
    names_row = google_sheets_api.get_table_data(settings.GS_KPI_TABLE_ID, sheet_name, "")[0]
    return {
        user_name: google_sheets_api.calc_cell_letter("A", i)
        for i, user_name in enumerate(names_row)
        if user_name and user_name != "Дата"
    }


def write_updated_kpi_data(users_stat: dict):
    """
    Функция записывает статистику сотрудника в соответствующую ячейку
    :param users_stat: статистика контактов, диалогов и лидов по сотрудникам
    """
    sheet_name = get_current_sheet_name()
    if sheet_name not in google_sheets_api.get_sheet_names(settings.GS_KPI_TABLE_ID):
        remove_inactive_users()
        create_kpi_sheet(users_stat.keys(), sheet_name)
    cell_num = get_cell_num_by_date(sheet_name)
    for user, column_name in get_kpi_user_cells(sheet_name).items():
        field_shifts = {"dialogs": 1, "leads": 3}
        for field, shift in field_shifts.items():
            cell_address = f"{google_sheets_api.calc_cell_letter(column_name, shift)}{cell_num}"
            google_sheets_api.write_to_google_sheet(
                [[users_stat[user][field]]],
                settings.GS_KPI_TABLE_ID,
                sheet_name,
                cell_address
            )


def append_kpi_new_user(user_name, index):
    """
    Функция добавляет колонку с сотрудников в уже существующую таблицу
    :param user_name: имя сотрудника
    :param index: порядковый номер сотрудника в списке сотрудников для добавления в таблицу
    :return:
    """
    sheet_name = get_current_sheet_name()
    sheet_id = google_sheets_api.get_sheet_id_by_name(
        settings.GS_KPI_TABLE_ID,
        sheet_name,
    )
    days_amount = get_current_month_days_amount()
    add_kpi_column(sheet_name, user_name, index, days_amount)
    merge_data = [
        google_sheets_api.get_merge_data(sheet_id, 0, 1, index * 4 + 1, index * 4 + 5),
        google_sheets_api.get_merge_data(sheet_id, 1, 2, index * 4 + 1, index * 4 + 3),
        google_sheets_api.get_merge_data(sheet_id, 1, 2, index * 4 + 3, index * 4 + 5),
        google_sheets_api.get_merge_data(
            sheet_id,
            google_sheets_api.KPI_TABLE_START_CELL_NUM + days_amount + 1,
            google_sheets_api.KPI_TABLE_START_CELL_NUM + days_amount + 2,
            index * 4 + 1,
            index * 4 + 5
        ),
    ]
    google_sheets_api.merge_cells(settings.GS_KPI_TABLE_ID, merge_data)
    google_sheets_api.add_borders(
        settings.GS_KPI_TABLE_ID,
        get_current_sheet_id(),
        0, days_amount + 6,
           index * 4 + 1, index * 4 + 5
    )


def get_current_sheet_name():
    """
    :return: Имя листа за текущий месяц
    """
    return (f"{google_sheets_api.MONTH_FROM_NUM[int(datetime.now().strftime('%m'))]} "
            f"{datetime.now().strftime('%Y')[-2:]}")


def get_current_sheet_id():
    """
        :return: id листа за текущий месяц
        """
    sheet_name = get_current_sheet_name()
    return google_sheets_api.get_sheet_id_by_name(
        settings.GS_KPI_TABLE_ID,
        sheet_name
    )


def get_current_month_days_amount():
    """
    :return: количество дней в текущем месяце
    """
    month, year = int(datetime.now().strftime('%m')), int(datetime.now().strftime('%Y'))
    return calendar.monthrange(year, month)[1]


def write_dates_column(sheet_name: str):
    """
    Запись в таблицу колонки с датами для статистики, а также "итого" и "премии"
    :param sheet_name: имя листа
    """
    google_sheets_api.write_to_google_sheet(
        [["Дата"]],
        settings.GS_KPI_TABLE_ID,
        sheet_name,
        f"A1:A{google_sheets_api.KPI_TABLE_START_CELL_NUM - 1}"
    )
    month, year = int(datetime.now().strftime('%m')), int(datetime.now().strftime('%Y'))
    days = [[date(year, month, day).strftime("%Y-%m-%d")] for day in range(1, get_current_month_days_amount() + 1)]
    days.append(["Итого"])
    days.append([])
    days.append(["Премии"])
    google_sheets_api.write_to_google_sheet(
        days,
        settings.GS_KPI_TABLE_ID,
        sheet_name,
        f"A{google_sheets_api.KPI_TABLE_START_CELL_NUM}:A{len(days) + google_sheets_api.KPI_TABLE_START_CELL_NUM}"
    )


def get_cell_num_by_date(sheet_name):
    """
    Возвращает номер строки в таблице для текущей даты
    :param sheet_name: название листа
    :return: номер строки текущей даты
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    return google_sheets_api.get_table_data(
        settings.GS_KPI_TABLE_ID,
        sheet_name,
        f"A{google_sheets_api.KPI_TABLE_START_CELL_NUM}:A{google_sheets_api.KPI_TABLE_FINISH_CELL_NUM}"
    ).index([current_date]) + google_sheets_api.KPI_TABLE_START_CELL_NUM


def get_kpi_users_list():
    """
    :return: список имен сотрудников с листа с сотрудниками
    """
    return [user[0] for user in google_sheets_api.get_table_data(
        settings.GS_KPI_TABLE_ID,
        settings.GS_KPI_USERS_SHEET_NAME,
        f"A:A"
    )[1:] if user]


def add_kpi_column(sheet_name, user_name, index, days_amount):
    """
    Добавляет в таблицу колонку с сотрудником при создании таблицы
    :param sheet_name: название листа
    :param user_name: имя сотрудника
    :param index: порядковый номер сотрудника
    :param days_amount: количество дней в текущеммесяце
    """
    data = google_sheets_api.get_table_data(
        settings.GS_KPI_TABLE_ID,
        settings.GS_KPI_USERS_SHEET_TEMPLATE_NAME,
        "B1:E6"
    )
    data[0].append(user_name)
    start_letter = google_sheets_api.calc_cell_letter('B', index * 4)
    for i in range(len(data[-3])):
        current_letter = google_sheets_api.calc_cell_letter(start_letter, i)
        data[-2][i] = (f'=СУММ({current_letter}{google_sheets_api.KPI_TABLE_START_CELL_NUM}'
                       f':{current_letter}{google_sheets_api.KPI_TABLE_START_CELL_NUM + days_amount - 1})')
    for i in range(2):
        current_letter = google_sheets_api.calc_cell_letter(start_letter, i * 2 + 1)
        data[-1][i * 2 + 1] = (
            f'={current_letter}'
            f'{google_sheets_api.KPI_TABLE_START_CELL_NUM + days_amount}-'
            f'{google_sheets_api.calc_cell_letter(current_letter, -1)}'
            f'{google_sheets_api.KPI_TABLE_START_CELL_NUM + days_amount}'
        )
    data[-1][2] = (
        f'={google_sheets_api.calc_cell_letter(start_letter, 3)}'
        f'{google_sheets_api.KPI_TABLE_START_CELL_NUM + days_amount + 1}/'
        f'{google_sheets_api.calc_cell_letter(start_letter, 1)}'
        f'{google_sheets_api.KPI_TABLE_START_CELL_NUM + days_amount + 1}'
    )
    for day in range(days_amount):
        data.insert(3, [])
    google_sheets_api.write_to_google_sheet(
        data,
        settings.GS_KPI_TABLE_ID,
        sheet_name,
        f"{start_letter}1:{google_sheets_api.calc_cell_letter(start_letter, 3)}{len(data) + 1}"
    )


def get_relevant_users():
    """
    Получает список актуальных сотрудников и в соответствии с ним корректирует список сотрудников в таблице
    :return: список актуальных сотрудников
    """
    relevant_users = get_kpi_users_list()
    for user in relevant_users:
        data = {"name": user}
        if not UsersKPI.objects.filter(**data).exists():
            serializer = UsersKPISerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                users_amount = UsersKPI.objects.all().count()
                append_kpi_new_user(user, users_amount - 1)
        else:
            serializer = UsersKPISerializer(UsersKPI.objects.get(**data))
            if not serializer.data["is_active"]:
                UsersKPI.objects.filter(pk=serializer.data["id"]).update(is_active=True)
    for user in UsersKPISerializer(UsersKPI.objects.all(), many=True).data:
        if user["name"] not in relevant_users:
            UsersKPI.objects.filter(pk=user["id"]).update(is_active=False)
    return [user["name"] for user in UsersKPISerializer(UsersKPI.objects.all(), many=True).data]


def update_kpi_statistics():
    """
    Запускает создание/обновление отчета по статистике сотрудников
    """
    end_time = datetime.now()
    start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
    user_names = get_relevant_users()
    users = skorozvon_api.get_users()
    if not users:
        return
    users_stat = dict()
    for user_name in user_names:
        if user_name in users:
            users_stat[user_name] = get_user_stat(
                start_time,
                end_time,
                users[user_name]
            )
        else:
            users_stat[user_name] = {
                "dialogs": "-",
                "leads": "-",
            }
    write_updated_kpi_data(users_stat)
