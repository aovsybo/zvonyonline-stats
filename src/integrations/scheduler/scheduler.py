from datetime import datetime
from dateutil.relativedelta import relativedelta

from ..models import Leads, QualifiedLeads, Dialogs
from ..services.skorozvon import skorozvon_api
from ..services.google_sheets import google_sheets_api

from apscheduler.schedulers.background import BackgroundScheduler


def get_db_contacts_count_for_interval(model, start_date, end_date, project_id):
    return (
        model.objects
        .filter(addDate__gte=start_date)
        .filter(addDate__lt=end_date)
        .filter(projectId=project_id)
        .count()
    )


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
    today = datetime.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_date = datetime.timestamp(today)
    end_date = datetime.timestamp(today + relativedelta(months=1))
    prev_start_date = datetime.timestamp(today - relativedelta(months=1))
    create_report_for_interval(start_date, end_date, prev_start_date)


def get_two_weeks_report():
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
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


def get_user_stat(start_time: float, end_time: float, user_id: int):
    return {
        "dialogs": 10,
        "leads": 3,
    }


def get_kpi_report():
    end_time = datetime.today()
    start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
    user_names = google_sheets_api.get_kpi_user_cells().keys()
    users_stat = dict()
    for user_name in user_names:
        users_stat[user_name] = get_user_stat(
            datetime.timestamp(start_time),
            datetime.timestamp(end_time),
            skorozvon_api.get_user_id_by_name(user_name)
        )
    google_sheets_api.create_kpi_report(users_stat)


def update_reports():
    # get_two_weeks_report()
    # get_month_report()
    get_kpi_report()


def start():
    scheduler = BackgroundScheduler()
    # scheduler.add_job(update_reports, 'interval', minutes=1)
    scheduler.add_job(update_reports, 'interval', seconds=10)
    scheduler.start()
