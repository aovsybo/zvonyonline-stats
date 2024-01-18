from datetime import datetime, timedelta

from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import CallInfoSerializer
from integrations.models import CallInfo
from integrations.service.skorozvon import SkorozvonAPI
from integrations.service.google_sheets import (
    create_main_sheet_copy,
    get_project_indexes,
    write_project_stat_to_google_sheet,
    write_prev_data_to_google_sheet,
    write_to_google_sheet,
    get_table_data
)


class CreateCallsAPIView(CreateAPIView):
    serializer_class = CallInfoSerializer

    # def post(self,  request):


def get_data_diapason(week: int):
    return (f"{(datetime.utcnow() - timedelta(weeks=week+2)).strftime('%d.%m.%y')}-"
            f"{(datetime.utcnow() - timedelta(weeks=week)).strftime('%d.%m.%y')}")


class WriteDataToGoogleSheet(ListAPIView):
    serializer_class = CallInfoSerializer
    queryset = CallInfo.objects.all()

    def get(self, request):
        # Получаем статистику со скорозвона
        skorozvon = SkorozvonAPI()
        projects_stat = skorozvon.get_projects_stat()
        # Копируем лист шаблон
        sheet_name = get_data_diapason(week=0)
        create_main_sheet_copy(sheet_name)
        # TODO: async
        write_project_stat_to_google_sheet(
            sheet_name=sheet_name,
            projects_stat=projects_stat,
            projects_indexes=get_project_indexes(),
        )
        write_prev_data_to_google_sheet(sheet_name, get_data_diapason(week=2))
        # getting prev projects data
        return Response(status=status.HTTP_200_OK)
