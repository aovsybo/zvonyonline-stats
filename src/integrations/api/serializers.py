from rest_framework import serializers

from ..models import Leads, Dialogs, QualifiedLeads


class LeadsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leads
        exclude = ('id',)


class DialogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dialogs
        exclude = ('id',)


class QualifiedLeadsSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualifiedLeads
        exclude = ('id',)
