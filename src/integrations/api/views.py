from datetime import datetime, timedelta

from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import LeadsSerializer
from integrations.models import Leads, QualifiedLeads, Dialogs
from integrations.services.skorozvon import skorozvon_api
from integrations.services.google_sheets import google_sheets_api


class WriteDataToGoogleSheet(ListAPIView):
    serializer_class = LeadsSerializer

    def get_queryset(self, model, start_date, project_id):
        return model.objects.filter(addDate__gt=start_date).filter(projectId=project_id).count()

    def get(self, request):
        # Получаем статистику со скорозвона
        projects_ids = skorozvon_api.get_projects_ids()
        start_date = int(datetime.timestamp(datetime.now() - timedelta(weeks=2)))
        projects_stat = dict()
        for project_name, project_id in projects_ids.items():
            projects_stat[project_name] = {
                "contacts": self.get_queryset(model=Leads, start_date=start_date, project_id=project_id),
                "dialogs": self.get_queryset(model=Dialogs, start_date=start_date, project_id=project_id),
                "leads": self.get_queryset(model=QualifiedLeads, start_date=start_date, project_id=project_id),
            }
        # TODO: Интерфейс готовый взять, кнопка в гугл талицах
        # TODO: async
        google_sheets_api.create_report_sheet(projects_stat)
        return Response(status=status.HTTP_200_OK)
