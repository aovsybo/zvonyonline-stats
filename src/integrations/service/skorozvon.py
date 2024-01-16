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


def get_call(call_id: int):
    token = get_token()
    headers = {
        "Authorization": token
    }
    url = f"https://app.skorozvon.ru/api/v2/calls/{call_id}"
    response = requests.get(url, headers=headers)
    return response.json()


def get_scenarios():
    token = get_token()
    headers = {
        "Authorization": token
    }
    url = f"https://app.skorozvon.ru/api/v2/scenarios"
    response = requests.get(url, headers=headers)
    return response.json()


def get_scenario(scenario_id: str):
    token = get_token()
    headers = {
        "Authorization": token
    }
    url = f"https://app.skorozvon.ru/api/v2/scenarios/{scenario_id}"
    response = requests.get(url, headers=headers)
    return response.json()


def get_calls():
    token = get_token()
    headers = {
        "Authorization": token
    }
    params = {
        "page": 1,
        "length": 100,
        "sort_by_time": True,
        "start_time": 1705185193,
        "sort_direction": "DESC"
    }
    url = f"https://app.skorozvon.ru/api/v2/calls/"
    response = requests.get(url, headers=headers, params=params)
    return response.json()
