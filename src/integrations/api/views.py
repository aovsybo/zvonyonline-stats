import json
import logging
from datetime import datetime

from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .serializers import CallDataInfoSerializer
from ..services.validation import ContactCreationData, LeadCreationData, flatten_data
from ..services.amocrm import send_lead_to_amocrm, is_working_amo_scenario, get_fields

logger = logging.getLogger(__name__)


class TestAPI(APIView):
    def post(self, request):
        # data = flatten_data(request.data)
        # validated_contact = ContactCreationData.model_validate(data)
        # validated_lead = LeadCreationData.model_validate(data)
        # send_lead_to_amocrm(validated_contact, validated_lead)
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
            validated_lead = LeadCreationData.model_validate(serializer.data)
            logger.info(f"request data: {request.data}\n"
                        f"request time: {datetime.now()}\n"
                        f"validated contact: {validated_contact}\n"
                        f"validated lead: {validated_lead}\n")
            send_lead_to_amocrm(validated_contact, validated_lead)
        return Response(status=status.HTTP_201_CREATED)
