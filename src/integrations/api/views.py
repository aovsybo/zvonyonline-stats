import json
import logging
from datetime import datetime

from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .serializers import CallDataInfoSerializer
from ..services.validation import ContactCreationData, flatten_data
from ..services.amocrm import send_lead_to_amocrm, is_working_amo_scenario

logger = logging.getLogger(__name__)


class TestAPI(APIView):
    def post(self, request):
        validated_contact = ContactCreationData.model_validate(flatten_data(request.data))
        send_lead_to_amocrm(validated_contact)
        return Response(status=status.HTTP_200_OK)


class WriteDataToGoogleSheet(CreateAPIView):
    serializer_class = CallDataInfoSerializer

    def post(self, request, *args, **kwargs):
        logger.info(json.dumps(request.data))
        serializer = self.serializer_class(data=flatten_data(request.data))
        if serializer.is_valid():
            serializer.save()
        if is_working_amo_scenario(serializer.data.get("call_scenario_id", "")):
            validated_contact = ContactCreationData.model_validate(serializer.data)
            logger.info(f"request_data: {request.data}\n"
                        f"request_time: {datetime.now()}\n"
                        f"validated_contact: {validated_contact}\n")
            send_lead_to_amocrm(validated_contact)
        return Response(status=status.HTTP_201_CREATED)
