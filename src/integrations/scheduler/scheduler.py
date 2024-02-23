from apscheduler.schedulers.background import BackgroundScheduler

from .kpi_statistics import get_kpi_report
from .dialogs_statistics import get_month_report, get_two_weeks_report


def get_intervals(count: int):
    intervals = []
    for i in range(count):
        intervals.append(",".join(
            [str(2 * (j * count + i)) for j in range(30 // count)]
        ))
    return intervals


def start():
    scheduler = BackgroundScheduler()
    jobs = [
        get_two_weeks_report,
        get_month_report,
        get_kpi_report
    ]
    intervals = get_intervals(len(jobs))
    for i, job in enumerate(jobs):
        scheduler.add_job(job, 'cron', minute=intervals[i])
    scheduler.start()
