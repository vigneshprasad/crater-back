from celery.schedules import crontab
from celery.task import periodic_task


@periodic_task(crontab(run_every="*/15"))
def update_user_leaderboards():
    pass


@periodic_task(run_every=crontab(hour="5", minute="30"))
def update_user_leaderboards_for_the_day():
    pass
