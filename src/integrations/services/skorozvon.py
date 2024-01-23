import requests

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
