from rest_framework import serializers

# from ..models import Leads, Dialogs, QualifiedLeads
from ..models import CallDataInfo, Leads


class CallDataInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallDataInfo
        fields = '__all__'


class LeadsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leads
        exclude = ('id',)
