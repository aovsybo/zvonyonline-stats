from datetime import datetime

from django.conf import settings

from ..models import CallDataInfo, Leads, UsersKPI


def get_user_stat(start_date: datetime, end_date: datetime, user_id: int) -> dict:
    """
    Считает статистику по совершенным звонкам сотрудника
    :param start_date:
    :param end_date:
    :param user_id: id сотрудника в скорозвоне
    :return: количество диалогов и лидов, проведенных сотрудником, за выбранный период времени
    """
    return {
        "dialogs": CallDataInfo.objects
        .filter(call_user_id=user_id)
        .filter(save_date__gte=start_date)
        .filter(save_date__lt=end_date)
        .filter(call_duration__gte=15)
        .count(),
        "leads": CallDataInfo.objects
        .filter(call_user_id=user_id)
        .filter(save_date__gte=start_date)
        .filter(save_date__lt=end_date)
        .filter(call_duration__gte=15)
        .filter(call_result_result_id__in=settings.SCOROZVON_WORKING_RESULT_IDS)
        .count()
    }


def get_db_contacts_count_for_interval(start_date, end_date, project_id):
    """
    :param start_date:
    :param end_date:
    :param project_id:
    :return: количество поступивших контактов
    """
    return (
        Leads.objects
        .filter(addDate__gte=start_date)
        .filter(addDate__lt=end_date)
        .filter(projectId=project_id)
        .count()
    )


# select count(distinct call_id) from integrations_calldatainfo where call_scenario_id='50000011958' and call_result_result_name in ('Отказ', 'Лид', 'Спорный', 'Успех') and save_date >= '2024-03-20 00:00:00' and save_date < '2024-03-21 00:00:00';
def get_db_dialogs_count_for_interval(start_date, end_date, scenario_id):
    """
    Считает диалоги по проекту за выбранный интервал. Диалог - любой разговор более 15 секунд,
    завершившийся отказом или успехом
    :param start_date:
    :param end_date:
    :param scenario_id:
    :return: количество проведенных диалогов
    """
    start_date = datetime.fromtimestamp(start_date)
    end_date = datetime.fromtimestamp(end_date)
    return (
        CallDataInfo.objects.filter(save_date__gte=start_date)
        .filter(save_date__lt=end_date)
        .filter(call_duration__ge=1)
        .filter(call_scenario_id=scenario_id)
        .filter(call_result_result_name__in=settings.SCOROZVON_DIALOG_RESULT_NAMES)
        .distinct("call_id")
        .count()
    )


def get_db_leads_count_for_interval(start_date, end_date, scenario_id):
    """
    Считает лиды по проекту за выбранный интервал. Лид - диалог, завершившийся успехом
    :param start_date:
    :param end_date:
    :param scenario_id:
    :return: количество полученных лидов
    """
    start_date = datetime.fromtimestamp(start_date)
    end_date = datetime.fromtimestamp(end_date)
    return (
        CallDataInfo.objects.filter(save_date__gte=start_date)
        .filter(save_date__lt=end_date)
        .filter(call_duration__ge=1)
        .filter(call_scenario_id=scenario_id)
        .filter(call_result_result_id__in=settings.SCOROZVON_WORKING_RESULT_IDS)
        .distinct("call_id")
        .count()
    )


def remove_inactive_users():
    UsersKPI.objects.filter(is_active=False).delete()
