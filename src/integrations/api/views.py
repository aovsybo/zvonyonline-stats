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


def get_current_time():
    current_local_time = datetime.utcnow() + timedelta(hours=4)
    return current_local_time.strftime("%H:%M")


class CreateCallsAPIView(CreateAPIView):
    serializer_class = CallInfoSerializer


def normalize_str(strs: list[str]):
    return sorted(list(map(lambda x: x.lower().replace(".", ""), strs)))


class WriteDataToGoogleSheet(ListAPIView):
    serializer_class = CallInfoSerializer
    queryset = CallInfo.objects.all()

    def get(self, request):
        data = dict()
        # sheet_name = get_current_time()
        # create_main_sheet_copy(sheet_name)
        # # TODO: async
        # write_project_stat_to_google_sheet(
        #     sheet_name=sheet_name,
        #     db_projects_info=self.serializer_class(self.get_queryset(), many=True).data,
        #     project_indexes=get_project_indexes(),
        # )
        calls = get_calls()["data"]
        data["s"] = []
        data["s"] = [(call["started_at"]["utc"], call["scenario_id"]) for call in calls]
        data["a"] = get_scenario("50000014058")

        # projects = list(get_project_indexes().keys())
        # # data["coins"] = [project for project in projects if project.lower().replace(".", "") in list(map(lower, ))]
        # data["1"] = normalize_str(scenarios)
        # data["2"] = normalize_str(projects)
        return Response(data=data, status=status.HTTP_200_OK)


def create_content():
    data = {
        'ЮСИ. Лидген с Авито РнД': 8,
        'ЮСИ. База РнД': 9,
        'ЮСИ. ГКЦ РнД': 10,
        'ЮСИ. Сайты ЖК РнД. (Проект с оплатой за лид)': 11,
        'ЮСИ. Лидген с Авито Ств': 13,
        'ЮСИ. ГКЦ Ств': 14,
        'ЮСИ. Сайты ЖК Ств. (Проект с оплатой за лид)': 15,
        'ЮСИ. Сайты ЖК Крд. (Проект с оплатой за лид)': 17,
        'ЮСИ. ГКЦ Крд': 18,
        'АН. База агенства Крд': 20,
        'АН. Сайты ЖК Крд. (Проект с оплатой за лид)': 21,
        'АН. ГЦК Крд': 22,
        'АН. ГЦК Рнд': 24
    }
