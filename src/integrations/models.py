from django.db import models
from django.utils import timezone


class CallDataInfo(models.Model):
    type = models.CharField(max_length=255)

    lead_id = models.CharField(max_length=255)
    lead_name = models.CharField(max_length=255)
    lead_comment = models.TextField(null=True, blank=True)
    lead_post = models.CharField(max_length=255, null=True, blank=True)
    lead_city = models.CharField(max_length=255, null=True, blank=True)
    lead_business = models.CharField(max_length=255, null=True, blank=True)
    lead_homepage = models.CharField(max_length=255, null=True, blank=True)
    lead_emails = models.JSONField(default=list)
    lead_inn = models.CharField(max_length=255, null=True, blank=True)
    lead_kpp = models.CharField(max_length=255, null=True, blank=True)
    lead_created_at = models.CharField(max_length=255, null=True)
    lead_updated_at = models.CharField(max_length=255, null=True)
    lead_deleted_at = models.CharField(max_length=255, null=True, blank=True)
    lead_parent_lead_id = models.CharField(max_length=255, null=True)
    lead_tags = models.JSONField(default=list)
    lead_phones = models.CharField(max_length=255)

    contact_id = models.CharField(max_length=255, blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    contact_comment = models.TextField(null=True, blank=True)
    contact_post = models.CharField(max_length=255, null=True, blank=True)
    contact_city = models.CharField(max_length=255, null=True, blank=True)
    contact_business = models.CharField(max_length=255, null=True, blank=True)
    contact_homepage = models.CharField(max_length=255, null=True, blank=True)
    contact_emails = models.JSONField(default=list)
    contact_inn = models.CharField(max_length=255, null=True, blank=True)
    contact_kpp = models.CharField(max_length=255, null=True, blank=True)
    contact_created_at = models.CharField(max_length=255, null=True)
    contact_updated_at = models.CharField(max_length=255, null=True)
    contact_deleted_at = models.CharField(max_length=255, null=True, blank=True)
    contact_parent_lead_id = models.CharField(max_length=255, blank=True)
    contact_tags = models.JSONField(default=list)
    contact_address = models.CharField(max_length=255, null=True, blank=True)
    contact_phones = models.CharField(max_length=255, blank=True)

    call_id = models.CharField(max_length=255)
    call_phone = models.CharField(max_length=255)
    call_source = models.CharField(max_length=255)
    call_direction = models.CharField(max_length=255, )
    call_params = models.JSONField(default=dict)
    call_lead_id = models.CharField(max_length=255)
    call_organization_id = models.CharField(max_length=255)
    call_user_id = models.CharField(max_length=255)
    call_started_at = models.CharField(max_length=255, null=True)
    call_connected_at = models.CharField(max_length=255, null=True)
    call_ended_at = models.CharField(max_length=255, null=True)
    call_reason = models.CharField(max_length=255)
    call_duration = models.IntegerField(null=True)
    call_scenario_id = models.CharField(max_length=255)
    call_result_id = models.CharField(max_length=255)
    call_incoming_phone = models.CharField(max_length=255, null=True, blank=True)
    call_recording_url = models.URLField(null=True, blank=True)
    call_call_type = models.CharField(max_length=255)
    call_region = models.CharField(max_length=255)
    call_local_time = models.CharField(max_length=255)
    call_call_project_id = models.CharField(max_length=255)
    call_call_project_title = models.CharField(max_length=255)
    call_scenario_result_group_id = models.CharField(max_length=255)
    call_scenario_result_group_title = models.CharField(max_length=255)

    call_result_result_id = models.CharField(max_length=255)
    call_result_result_name = models.CharField(max_length=255)
    call_result_comment = models.TextField(null=True)

    save_date = models.DateTimeField(default=timezone.localtime(timezone.now()))


class Leads(models.Model):
    id = models.IntegerField(primary_key=True, auto_created=True)
    name = models.CharField(max_length=255, blank=True)
    phoneNumber = models.CharField(max_length=255, blank=True)
    site = models.CharField(max_length=255, blank=True)
    comment = models.CharField(max_length=255, blank=True)
    projectId = models.CharField(max_length=100, blank=True)
    addDate = models.IntegerField(blank=True)

    class Meta:
        managed = False
        db_table = 'Leads'
