from django.db import models


class Leads(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    site = models.CharField(max_length=255)
    comment = models.CharField(max_length=255)
    project_id = models.IntegerField()
    add_date = models.IntegerField()
