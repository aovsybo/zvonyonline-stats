import requests
import aiohttp
import asyncio

from datetime import datetime, timedelta
import time

from django.conf import settings


class SkorozvonAPI:
    API_URL = f"https://app.skorozvon.ru/api/v2/"
    _token = None

    def __init__(self):
        self._token = self.get_token()

    def get_token(self):
        token_url = "https://app.skorozvon.ru/oauth/token"
        data = {
            "grant_type": "password",
            "username": settings.SKOROZVON_LOGIN,
            "api_key": settings.SKOROZVON_API_KEY,
            "client_id": settings.SKOROZVON_APPLICATION_ID,
            "client_secret": settings.SKOROZVON_APPLICATION_KEY,
        }
        response = requests.post(token_url, data=data).json()
        return f"Bearer {response['access_token']}"

    def get_request(self, sub_url: str, params: dict = None):
        return requests.get(
            url=f"{self.API_URL}{sub_url}",
            headers={"Authorization": self._token},
            params=params
        ).json()

    async def get_async_request(self, session, sub_url: str, params: dict = None):
        async with session.get(
                url=f"{self.API_URL}{sub_url}",
                headers={"Authorization": self._token},
                params=params
        ) as response:
            return await response.json(content_type=None)

    def get_scenarios_ids(self):
        response = self.get_request(
            sub_url="scenarios",
            params={"length": 100},
        )
        return {
            project["name"]: project["id"]
            for project in response["data"]
            if project["name"] in settings.SKOROZVON_SCENARIO_TO_GS_NAME.keys()
        }

    def get_projects_ids(self):
        response = self.get_request(
            sub_url="call_projects",
            params={"length": 100},
        )
        return {
            project["title"]: project["id"]
            for project in response["data"]
            if project["title"] in settings.SKOROZVON_PROJECT_TO_GS_NAME.keys()
        }

    #
    # async def get_one_project_stat_by_id(self, session, project_id: str, start_time: int):
    #     return await self.get_async_request(
    #         session=session,
    #         sub_url=f"call_projects/{project_id}/statistic",
    #         params={"start_time": start_time},
    #     )

    def get_calls(self, project_id: int, start_time: int):
        params = {
            "page": 1,
            "length": 100,
            "sort_by_time": True,
            "start_time": start_time,
            "sort_direction": "DESC",

        }
        return self.get_request("calls", params)

    # async def create_async_projects_stat_tasks(self, start_time: int):
    #     async with aiohttp.ClientSession() as session:
    #         tasks = [
    #             asyncio.create_task(self.get_one_project_stat_by_id(session, project_id, start_time))
    #             for project_id in self.get_projects_ids()
    #         ]
    #         return await asyncio.gather(*tasks)

    # def get_projects_stat(self):
    #     start_time = int(time.mktime((datetime.now() - timedelta(hours=1)).timetuple()))
    #     projects_stat = asyncio.run(self.create_async_projects_stat_tasks(start_time))
    #     return {
    #         settings.SKOROZVON_TO_GS_NAME[project["title"]]: {
    #             "contacts": project["cases_count"],
    #             "dialogs": project["completed_cases_count"],
    #             "leads": 1,
    #         }
    #         for project in projects_stat
    #     }
