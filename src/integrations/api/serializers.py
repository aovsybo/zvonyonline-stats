from rest_framework import serializers

from integrations.models import Leads


class LeadsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leads
        fields = '__all__'
