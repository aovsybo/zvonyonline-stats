from datetime import datetime, timedelta

from rest_framework.generics import CreateAPIView, ListAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import LeadsSerializer
from integrations.models import Leads
from integrations.service.skorozvon import SkorozvonAPI
from integrations.service.google_sheets import (
    create_main_sheet_copy,
    get_project_indexes,
    write_project_stat_to_google_sheet,
    write_prev_data_to_google_sheet,
    write_to_google_sheet,
    get_sz_to_gs_data
)


def get_data_diapason(week: int):
    return (f"{(datetime.utcnow() - timedelta(weeks=week+2)).strftime('%d.%m.%y')}-"
            f"{(datetime.utcnow() - timedelta(weeks=week)).strftime('%d.%m.%y')}")


class WriteDataToGoogleSheet(ListAPIView):
    serializer_class = LeadsSerializer

    def get_queryset(self, start_date, project_id):
        return Leads.objects.filter(addDate__gt=start_date).filter(projectId=project_id)

    def get(self, request):
        # Получаем статистику со скорозвона
        skorozvon = SkorozvonAPI()
        projects_ids = skorozvon.get_projects_ids()
        start_date = int(datetime.timestamp(datetime.now() - timedelta(weeks=2)))
        data = dict()
        for project_name, project_id in projects_ids.items():
            project_calls_ids = list(self.serializer_class(self.get_queryset(
                start_date=start_date,
                project_id=project_id
            ), many=True).data)
            data[project_name] = dict()
            data[project_name]["contacts"] = len(project_calls_ids)
            data[project_name]["dialogs"] = int(len(project_calls_ids) * 0.8)
            data[project_name]["leads"] = int(len(project_calls_ids) * 0.1)
        # Копируем лист шаблон
        # sheet_name = get_data_diapason(week=0)
    #     create_main_sheet_copy(sheet_name)
    #     # TODO: Заменить проекты на сценарии
    #     # TODO: async
    #     write_project_stat_to_google_sheet(
    #         sheet_name=sheet_name,
    #         projects_stat=projects_stat,
    #         projects_indexes=get_project_indexes(),
    #     )
    #     write_prev_data_to_google_sheet(sheet_name, get_data_diapason(week=2))
        return Response(data=data, status=status.HTTP_200_OK)
