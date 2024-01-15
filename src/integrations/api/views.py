from  datetime import datetime, timedelta

from django.conf import settings
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import CallInfoSerializer
from integrations.models import CallInfo
from integrations.service.skorozvon import get_calls
from integrations.service.google_sheets import (
    create_main_sheet_copy,
    get_project_indexes,
    write_to_cell_google_sheet,
)


def get_current_time():
    current_local_time = datetime.utcnow() + timedelta(hours=4)
    return current_local_time.strftime("%H:%M")


class CreateCallsAPIView(CreateAPIView):
    serializer_class = CallInfoSerializer


class WriteDataToGoogleSheet(ListAPIView):
    serializer_class = CallInfoSerializer
    queryset = CallInfo.objects.all()

    def get(self, request):
        data = dict()
        db_projects_info = self.serializer_class(self.get_queryset(), many=True).data
        working_sheet_id = create_main_sheet_copy(get_current_time())
        # data["worksheet"] = working_sheet_id
        project_indexes = get_project_indexes()
        response = []
        # write_to_cell_google_sheet("aaa", settings.GS_TABLE_ID, "Шаблон", "A77")
        # for project_info in db_projects_info:
        #     cell_num = project_indexes[project_info["project_name"]]
        #     write_to_google_sheet()
        #     response.append(f"{project_info['project_name']} "
        #      f"C{cell_num}: {project_info['contacts']} "
        #      f"F{cell_num}: {project_info['dialogs']} "
        #      f"J{cell_num}: {project_info['leads']}")
        # data["response"] = response
        return Response(data=data, status=status.HTTP_200_OK)

