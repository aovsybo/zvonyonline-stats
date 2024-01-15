from rest_framework import serializers

from integrations.models import CallInfo


class CallInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallInfo
        fields = '__all__'
