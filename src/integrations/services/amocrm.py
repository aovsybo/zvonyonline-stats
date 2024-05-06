import json
import requests
import time

from django.conf import settings

from .validation import ContactCreationData, LeadCreationData
from . import amo_db


LEAD_FIELDS_IDS = {
    1444017: "comment",
}

CONTACT_FIELDS_IDS = {
}

AMO_WORKING_SCENARIOS_IDS = [
    "50000014598",
    "50000014725",
]
AMO_WORKING_RESULTS_IDS = [
    "50000014598",
    "50000261928",
]


def save_token_data(data: dict):
    url = f"https://{settings.AMO_INTEGRATION_SUBDOMAIN}.amocrm.ru/oauth2/access_token"
    response = requests.post(url, json=data).json()
    data = {
        "access_token": response['access_token'],
        "refresh_token": response['refresh_token'],
        "token_type": response['token_type'],
        "expires_in": response['expires_in'],
        "end_token_time": response['expires_in'] + time.time(),
    }
    with open(settings.BASE_DIR / 'refresh_token.txt', 'w') as outfile:
        json.dump(data, outfile)
    return data["access_token"]


def auth():
    data = {
        'client_id': settings.AMO_INTEGRATION_CLIENT_ID,
        'client_secret': settings.AMO_INTEGRATION_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': settings.AMO_INTEGRATION_CODE,
        'redirect_uri': settings.AMO_INTEGRATION_REDIRECT_URI,
    }
    return save_token_data(data)


def get_fields(postfix: str):
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
    }
    link = f"/api/v4/{postfix}/custom_fields"
    url = f"https://{settings.AMO_INTEGRATION_SUBDOMAIN}.amocrm.ru{link}"
    return requests.get(url, headers=headers).json()


def update_access_token(refresh_token: str):
    data = {
        "client_id": settings.AMO_INTEGRATION_CLIENT_ID,
        "client_secret": settings.AMO_INTEGRATION_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "redirect_uri": settings.AMO_INTEGRATION_REDIRECT_URI,
    }
    return save_token_data(data)


def get_access_token():
    with open(settings.BASE_DIR / 'refresh_token.txt') as json_file:
        token_info = json.load(json_file)
        if token_info["end_token_time"] - 60 < time.time():
            return update_access_token(token_info["refresh_token"])
        else:
            return dict(token_info)["access_token"]


def get_custom_fields_values(field_ids: dict, data):
    custom_fields_values = []
    data = data.dict()
    for field_id, field_name in field_ids.items():
        custom_fields_values.append({
            "field_id": field_id,
            "values": [{"value": data[field_name]}]
        })
    return custom_fields_values


def get_or_create_contact(validated_data):
    if amo_db.contact_exists(validated_data.phone):
        contact_id = amo_db.get_contact_id_by_phone(validated_data.phone)
    else:
        contact_id = create_contact(validated_data)
        amo_db.create_contact(contact_id=contact_id, phone=validated_data.phone)
    return contact_id


def create_contact(contact: ContactCreationData):
    custom_fields = get_custom_fields_values(CONTACT_FIELDS_IDS, contact)
    custom_fields.append({
      "field_id": 104057,
      "values": [
        {
          "value": contact.phone,
          "enum_code": "WORK"
        }
      ]
    })
    body = [{
        "name": contact.name,
        "responsible_user_id": 10892178,
        "custom_fields_values": custom_fields,
    }]
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
    }
    url = f"https://{settings.AMO_INTEGRATION_SUBDOMAIN}.amocrm.ru/api/v4/contacts"
    return requests.post(url, json=body, headers=headers).json()['_embedded']['contacts'][0]['id']


def create_lead(contact_id, lead: LeadCreationData, contact: ContactCreationData):
    custom_fields = get_custom_fields_values(LEAD_FIELDS_IDS, lead)
    custom_fields.append({
        "field_id": 1432107,
        "values": [{"value": contact.name}]
    })
    body = [{
        "name": f"Звони онлайн {contact.phone}",
        "pipeline_id": settings.AMO_LEAD_PIPELINE_ID,
        "status_id": settings.AMO_LEAD_STATUS_ID,
        "Компания": contact.phone,
        "_embedded": {
            "contacts": [{"id": contact_id}]
        },
        "responsible_user_id": 10892178,
        "custom_fields_values": custom_fields
    }]
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
    }
    url = f"https://{settings.AMO_INTEGRATION_SUBDOMAIN}.amocrm.ru/api/v4/leads"
    return requests.post(url, json=body, headers=headers).json()


def send_lead_to_amocrm(contact: ContactCreationData, lead: LeadCreationData):
    contact_id = get_or_create_contact(contact)
    return create_lead(contact_id, lead, contact)


def is_lead(scenario_id: str, result_id: str):
    return is_working_scenario_id(scenario_id) and is_working_result_id(result_id)


def is_working_result_id(result_id: str):
    return True if result_id in AMO_WORKING_RESULTS_IDS else False


def is_working_scenario_id(scenario_id: str):
    return True if scenario_id in AMO_WORKING_SCENARIOS_IDS else False
