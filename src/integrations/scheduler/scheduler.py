from datetime import datetime
from dateutil.relativedelta import relativedelta

from ..models import Leads, QualifiedLeads, Dialogs
from ..services.skorozvon import skorozvon_api
from ..services.google_sheets import google_sheets_api

from apscheduler.schedulers.background import BackgroundScheduler


def get_db_contacts_count_for_interval(model, start_date, end_date, project_id):
    return (model.objects
            .filter(addDate__gte=start_date)
            .filter(addDate__lt=end_date)
            .filter(projectId=project_id)
            .count())


def create_report_for_interval(start_date, end_date, prev_start_date):
    projects_ids = skorozvon_api.get_projects_ids()
    projects_stat = dict()
    for project_name, project_id in projects_ids.items():
        projects_stat[project_name] = {
            "contacts": get_db_contacts_count_for_interval(
                model=Leads,
                start_date=start_date,
                end_date=end_date,
                project_id=project_id
            ),
            "dialogs": get_db_contacts_count_for_interval(
                model=Dialogs,
                start_date=start_date,
                end_date=end_date,
                project_id=project_id
            ),
            "leads": get_db_contacts_count_for_interval(
                model=QualifiedLeads,
                start_date=start_date,
                end_date=end_date,
                project_id=project_id
            ),
        }
    google_sheets_api.create_report_sheet(projects_stat, start_date, end_date, prev_start_date)


def get_month_report():
    today = datetime.today().replace(day=1)
    start_date = datetime.timestamp(today)
    end_date = datetime.timestamp(today + relativedelta(months=1))
    prev_start_date = datetime.timestamp(today - relativedelta(months=1))
    create_report_for_interval(start_date, end_date, prev_start_date)


def get_two_weeks_report():
    today = datetime.today()
    if today.day > 15:
        two_weeks_ago = today.replace(day=16)
        today = (today + relativedelta(months=1)).replace(day=1)
    else:
        two_weeks_ago = today.replace(day=1)
        today = today.replace(day=16)
    start_date = datetime.timestamp(two_weeks_ago)
    end_date = datetime.timestamp(today)
    prev_start_date = datetime.timestamp(today - relativedelta(months=1))
    create_report_for_interval(start_date, end_date, prev_start_date)


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(get_month_report, 'cron', minute="53")
    scheduler.add_job(get_two_weeks_report, 'cron', minute="54")
    scheduler.start()
