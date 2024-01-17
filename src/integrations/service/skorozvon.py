import requests

from django.conf import settings


def get_token():
    url = "https://app.skorozvon.ru/oauth/token"
    data = {
        "grant_type": "password",
        "username": settings.SKOROZVON_LOGIN,
        "api_key": settings.SKOROZVON_API_KEY,
        "client_id": settings.SKOROZVON_APPLICATION_ID,
        "client_secret": settings.SKOROZVON_APPLICATION_KEY,
    }
    token = requests.post(url, data=data).json()
    return f"Bearer {token['access_token']}"


def get_request(sub_url: str, params: dict = None):
    headers = {
        "Authorization": get_token()
    }
    response = requests.get(url=f"https://app.skorozvon.ru/api/v2/{sub_url}", headers=headers, params=params)
    return response.json()


def get_call(call_id: int):
    return get_request(f"calls/{call_id}")


def get_scenarios():
    return get_request("scenarios")


def get_scenario(scenario_id: str):
    return get_request(f"scenarios/{scenario_id}")


def get_calls():
    params = {
        "page": 1,
        "length": 100,
        "sort_by_time": True,
        "start_time": 1705185193,
        "sort_direction": "DESC"
    }
    return get_request("calls", params)
