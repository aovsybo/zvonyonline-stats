from django.db import models


class Leads(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    phoneNumber = models.CharField(max_length=255, blank=True, null=True)
    site = models.CharField(max_length=255, blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    projectId = models.CharField(max_length=100, blank=True, null=True)
    addDate = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Leads'


class QualifiedLeads(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    phoneNumber = models.CharField(max_length=255, blank=True, null=True)
    site = models.CharField(max_length=255, blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    projectId = models.CharField(max_length=100, blank=True, null=True)
    addDate = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'QualifiedLeads'


class Dialogs(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    phoneNumber = models.CharField(max_length=255, blank=True, null=True)
    site = models.CharField(max_length=255, blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    projectId = models.CharField(max_length=100, blank=True, null=True)
    addDate = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Dialogs'
