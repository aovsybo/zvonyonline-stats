from datetime import datetime

from django.conf import settings

from ..models import CallDataInfo, Leads


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


def get_db_dialogs_count_for_interval(start_date, end_date, project_id):
    """
    Считает диалоги по проекту за выбранный интервал. Диалог - любой разговор более 15 секунд,
    завершившийся отказом или успехом
    :param start_date:
    :param end_date:
    :param project_id:
    :return: количество проведенных диалогов
    """
    start_date = datetime.fromtimestamp(start_date)
    end_date = datetime.fromtimestamp(end_date)
    return (
        CallDataInfo.objects.filter(save_date__gte=start_date)
        .filter(save_date__lt=end_date)
        .filter(call_call_project_id=project_id)
        .filter(call_result_result_name__in=settings.SCOROZVON_WORKING_DIALOG_RESULT_NAMES)
        .filter(call_scenario_id__in=settings.SCOROZVON_WORKING_SCENARIO_IDS)
        .count()
    )


def get_db_leads_count_for_interval(start_date, end_date, project_id):
    """
    Считает лиды по проекту за выбранный интервал. Лид - диалог, завершившийся успехом
    :param start_date:
    :param end_date:
    :param project_id:
    :return: количество полученных лидов
    """
    start_date = datetime.fromtimestamp(start_date)
    end_date = datetime.fromtimestamp(end_date)
    return (
        CallDataInfo.objects.filter(save_date__gte=start_date)
        .filter(save_date__lt=end_date)
        .filter(call_call_project_id=project_id)
        .filter(call_scenario_id__in=settings.SCOROZVON_WORKING_SCENARIO_IDS)
        .filter(call_result_result_id__in=settings.SCOROZVON_WORKING_RESULT_IDS)
        .count()
    )
