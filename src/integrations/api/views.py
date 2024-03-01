import json
import logging

from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import CallDataInfoSerializer


logger = logging.getLogger(__name__)

# TODO: debug false on prod
# TODO: rm inactive users when create google sheet


class Test(ListAPIView):
    def get(self, request, *args, **kwargs):
        data = dict()
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
