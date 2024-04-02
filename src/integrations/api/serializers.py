from rest_framework import serializers

from ..models import CallDataInfo, Leads, UsersKPI, ProjectInfo


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


class ProjectInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectInfo
        fields = '__all__'
