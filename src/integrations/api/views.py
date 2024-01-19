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


class CreateCallsAPIView(CreateAPIView, UpdateAPIView):
    # serializer_class = LeadsSerializer
    def post(self):
      return Response(status=status.HTTP_200_OK)


def get_data_diapason(week: int):
    return (f"{(datetime.utcnow() - timedelta(weeks=week+2)).strftime('%d.%m.%y')}-"
            f"{(datetime.utcnow() - timedelta(weeks=week)).strftime('%d.%m.%y')}")


class WriteDataToGoogleSheet(ListAPIView):
    serializer_class = LeadsSerializer
    queryset = Leads.objects.all()[:10]

    # def get(self, request):
    #     skorozvon = SkorozvonAPI()
    #     data = skorozvon.get_scenarios_ids()
    #     return Response(data=data, status=status.HTTP_200_OK)

    # def get(self, request):
    #     # Получаем статистику со скорозвона
    #     skorozvon = SkorozvonAPI()
    #     # projects_stat = skorozvon.get_projects_stat()
    #     projects_stat = list(self.serializer_class(self.get_queryset(), many=True).data)
    #     # Копируем лист шаблон
    #     sheet_name = get_data_diapason(week=0)
    #     create_main_sheet_copy(sheet_name)
    #     # TODO: Заменить проекты на сценарии
    #     # TODO: Парсить данные из существующей БД
    #     # TODO: async
    #     write_project_stat_to_google_sheet(
    #         sheet_name=sheet_name,
    #         projects_stat=projects_stat,
    #         projects_indexes=get_project_indexes(),
    #     )
    #     write_prev_data_to_google_sheet(sheet_name, get_data_diapason(week=2))
    #     return Response(status=status.HTTP_200_OK)
