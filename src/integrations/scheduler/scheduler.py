from apscheduler.schedulers.background import BackgroundScheduler

from .kpi_statistics import update_kpi_statistics
from .dialogs_statistics import (
    update_month_dialog_statistics,
    update_two_weeks_dialog_statistics,
    sync_projects_info
)


def get_intervals(count: int):
    intervals = []
    for i in range(count):
        intervals.append(",".join(
            [str(2 * (j * count + i)) for j in range(30 // count)]
        ))
    return intervals


def start():
    pass
    # scheduler = BackgroundScheduler()
    # jobs = [
    #     sync_projects_info,
    #     update_two_weeks_dialog_statistics,
    #     update_month_dialog_statistics,
    #     update_kpi_statistics
    # ]
    # intervals = get_intervals(len(jobs))
    # for i, job in enumerate(jobs):
    #     scheduler.add_job(job, 'cron', minute=intervals[i])
    # scheduler.start()
