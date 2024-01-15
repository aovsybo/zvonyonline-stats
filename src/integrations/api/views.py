from  datetime import datetime, timedelta

from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import CallInfoSerializer
from integrations.models import CallInfo
from integrations.service.skorozvon import get_calls
from integrations.service.google_sheets import (
    get_table_data,
    write_to_google_sheet,
    create_sheet_copy,
    create_main_sheet_copy,
    update_sheet_name,
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
        data["objects"] = self.serializer_class(self.get_queryset(), many=True).data
        working_sheet_id = create_main_sheet_copy(get_current_time())
        data["worksheet"] = working_sheet_id
        return Response(data=data, status=status.HTTP_200_OK)

