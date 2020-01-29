from __future__ import absolute_import, unicode_literals

from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from .models import Subscription


@shared_task(name="check_subscription")
def check_subscription(phone_number, message):
    date = timezone.now().date()
    subs = Subscription.objects.filtre(date_end__lt=date, is_active=True)
    subs.update(is_active=False)
    for sub in subs:
        sub.is_active = False
        trial_sub = sub.user.subscriptions.filter(is_trial=True)
        if not trial_sub.exists():
            Subscription.objects.create(
                user=sub.user,
                is_trial=True,
                date_start=date,
                date_end=date + relativedelta(months=31)
            )
