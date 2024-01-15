from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from integrations.service.skorozvon import get_calls
from integrations.service.google_sheets import (
    get_table_data,
    write_to_google_sheet,
    create_sheet_copy,
    create_main_sheet_copy,
    update_sheet_name,
)


class PostDataToTable(APIView):
    def get(self, request):
        data = dict()
        sheet_id = "1607843362"
        new_name = "new name"
        # data["table"] = update_sheet_name(
        #     sheet_id,
        #     new_name
        # )
        data["table"] = create_main_sheet_copy("boba")
        return Response(data=data, status=status.HTTP_200_OK)


