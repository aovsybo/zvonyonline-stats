from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import LeadsSerializer


class WriteDataToGoogleSheet(ListAPIView):
    serializer_class = LeadsSerializer

    def post(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK)
