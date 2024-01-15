from django.db import models


class CallInfo(models.Model):
    project_name = models.CharField(max_length=255)
    contacts = models.IntegerField(default=0)
    dialogs = models.IntegerField(default=0)
    leads = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
