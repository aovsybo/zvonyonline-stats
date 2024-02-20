from rest_framework import serializers

from ..models import CallDataInfo, Leads, UsersKPI


class UsersKPISerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersKPI
        fields = '__all__'


class CallDataInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallDataInfo
        fields = '__all__'


class LeadsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leads
        exclude = ('id',)
