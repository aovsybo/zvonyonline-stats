from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status

from ..services.google_sheets import google_sheets_api

from .serializers import LeadsSerializer


class WriteDataToGoogleSheet(ListAPIView):
    # @staticmethod
    # def get_db_contacts_count_for_interval(model, start_date, end_date, project_id):
    #     return (model.objects
    #             .filter(addDate__gte=start_date)
    #             .filter(addDate__lt=end_date)
    #             .filter(projectId=project_id)
    #             .count())
    serializer_class = LeadsSerializer

    def get(self, request, *args, **kwargs):
        data = dict()
        data["props"] = google_sheets_api.get_sheet_properties()
        return Response(data=data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # projects_ids = skorozvon_api.get_projects_ids()
        # start_date = request.data.get("start_date")
        # end_date = request.data.get("end_date")
        # projects_stat = dict()
        # for project_name, project_id in projects_ids.items():
        #     projects_stat[project_name] = {
        #         "contacts": self.get_db_contacts_count_for_interval(
        #             model=Leads,
        #             start_date=start_date,
        #             end_date=end_date,
        #             project_id=project_id
        #         ),
        #         "dialogs": self.get_db_contacts_count_for_interval(
        #             model=Dialogs,
        #             start_date=start_date,
        #             end_date=end_date,
        #             project_id=project_id
        #         ),
        #         "leads": self.get_db_contacts_count_for_interval(
        #             model=QualifiedLeads,
        #             start_date=start_date,
        #             end_date=end_date,
        #             project_id=project_id
        #         ),
        #     }
        # google_sheets_api.create_report_sheet(projects_stat)
        return Response(status=status.HTTP_200_OK)
