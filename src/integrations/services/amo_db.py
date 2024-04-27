from ..models import CRMContact
from ..api.serializers import CRMContactSerializer


def contact_exists(phone: str) -> bool:
    return CRMContact.objects.filter(phone=phone).exists()


def get_contact_id_by_phone(phone: str) -> int:
    instance = CRMContact.objects.get(phone=phone)
    field_object = CRMContact._meta.get_field("contact_id")
    return field_object.value_from_object(instance)


def create_contact(contact_id: int, phone: str):
    serializer = CRMContactSerializer(data={
        "contact_id": contact_id,
        "phone": phone
    })
    if serializer.is_valid():
        serializer.save()
