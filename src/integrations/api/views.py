import json
import logging

from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import CallDataInfoSerializer


logger = logging.getLogger(__name__)


class Test(ListAPIView):
    def get(self, request, *args, **kwargs):
        data = dict()
        from ..services.google_sheets import google_sheets_api
        from ..scheduler.scheduler import get_relevant_users
        user_names = get_relevant_users()
        import datetime
        data["asd"] = google_sheets_api._crate_kpi_sheet(user_names, str(datetime.datetime.timestamp(datetime.datetime.now())))
        return Response(data=data, status=status.HTTP_201_CREATED)


class WriteDataToGoogleSheet(CreateAPIView):
    serializer_class = CallDataInfoSerializer

    def post(self, request, *args, **kwargs):
        logger.info(json.dumps(request.data))
        serializer = self.serializer_class(data=self.flatten_data(request.data))
        if serializer.is_valid():
            serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    @staticmethod
    def flatten_data(y):
        out = {}

        def flatten(x, name=''):
            if type(x) is dict:
                for a in x:
                    flatten(x[a], name + a + '_')
            elif type(x) is list:
                i = 0
                for a in x:
                    flatten(a, name + str(i) + '_')
                    i += 1
            else:
                out[name[:-1]] = x

        flatten(y)
        return out
