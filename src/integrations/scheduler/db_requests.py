from datetime import datetime

from django.conf import settings

from ..models import CallDataInfo, Leads, UsersKPI, ProjectInfo
from ..api.serializers import ProjectInfoSerializer


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
        .filter(call_duration__gte=1)
        .filter(call_scenario_id=scenario_id)
        .filter(call_result_result_name__in=settings.SCOROZVON_DIALOG_RESULT_NAMES)
        .values('call_id')
        .distinct()
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
        .filter(call_duration__gte=1)
        .filter(call_scenario_id=scenario_id)
        .filter(call_result_result_id__in=settings.SCOROZVON_WORKING_RESULT_IDS)
        .values('call_id')
        .distinct()
        .count()
    )


def remove_inactive_users():
    UsersKPI.objects.filter(is_active=False).delete()


def deactivate_irrelevant_projects(project_titles):
    projects = ProjectInfo.objects.filter(is_active=True)
    projects_data = ProjectInfoSerializer(projects, many=True).data
    for project in projects_data:
        if project["project_title"] not in project_titles:
            project_instance = ProjectInfo.objects.get(id=project["id"])
            project_instance.is_active = False
            project_instance.save()


def update_projects_info(projects_info: list[dict]):
    deactivate_irrelevant_projects([project["project_title"] for project in projects_info])
    for project_info in projects_info:
        if ProjectInfo.objects.filter(project_title=project_info["project_title"]).exists():
            project_instance = ProjectInfo.objects.get(project_title=project_info["project_title"])
            serializer = ProjectInfoSerializer(project_instance)
            if serializer.data != project_info:
                serializer.update(project_instance, project_info)
        else:
            serializer = ProjectInfoSerializer(data=project_info)
            if serializer.is_valid():
                serializer.save()


def get_active_project_titles():
    active_projects = ProjectInfo.objects.filter(is_active=True)
    active_projects_data = ProjectInfoSerializer(active_projects, many=True).data
    return [project["project_title"] for project in active_projects_data]


def get_projects_info_by_title(project_title: str):
    project = ProjectInfo.objects.get(project_title=project_title)
    return ProjectInfoSerializer(project).data
