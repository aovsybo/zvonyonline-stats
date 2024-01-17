from datetime import datetime, timedelta

from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import CallInfoSerializer
from integrations.models import CallInfo
from integrations.service.skorozvon import (
    get_call,
    get_calls,
    get_scenarios,
    get_scenario,
)
from integrations.service.google_sheets import (
    create_main_sheet_copy,
    get_project_indexes,
    write_project_stat_to_google_sheet,
)


class CreateCallsAPIView(CreateAPIView):
    serializer_class = CallInfoSerializer

    # def post(self,  request):
    #     calls = get_call("50648663900")


class WriteDataToGoogleSheet(ListAPIView):
    serializer_class = CallInfoSerializer
    queryset = CallInfo.objects.all()

    def get(self, request):
        sheet_name = (datetime.utcnow() + timedelta(hours=4)).strftime("%H:%M")
        create_main_sheet_copy(sheet_name)
        # TODO: async
        write_project_stat_to_google_sheet(
            sheet_name=sheet_name,
            db_projects_info=self.serializer_class(self.get_queryset(), many=True).data,
            project_indexes=get_project_indexes(),
        )
        return Response(status=status.HTTP_200_OK)
