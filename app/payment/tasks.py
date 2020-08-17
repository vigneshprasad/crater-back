from __future__ import absolute_import, unicode_literals

import datetime

from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from utils.stripe_service import stripe_service
from .models import Subscription


@shared_task(name='charge_subscription_payment')
def charge_subscription_payment(user_pk):
    from users.models import User
    try:
        user = User.objects.get(pk=user_pk)
        date = timezone.now().date()
        if not user.has_active_subscription:
            customer_id = None
            membership = 'basic'
            if hasattr(user, 'bank_details') and user.bank_details:
                customer_id = user.bank_details.stripe_customer_id
                membership = user.bank_details.membership
            if customer_id:
                charge = None
                amount = 350000 if membership == 'premium' else 250000
                try:
                    charge = stripe_service.create_customer_charge(
                        customer_id=customer_id,
                        amount=amount,
                        description='New Subscription payment'
                    )
                except:
                    pass
                if charge and charge.paid:
                    Subscription.objects.create(
                        user=user,
                        date_start=date,
                        date_end=date + relativedelta(years=1),
                        membership=membership
                    )
    except User.DoesNotExist:
        pass


@shared_task(name="check_subscription")
def check_subscription():
    date = timezone.now().date()
    subs = Subscription.objects.filter(date_end__lt=date, is_active=True)
    subs.update(is_active=False)
    for sub in subs:
        sub.is_active = False
        trial_sub = sub.user.subscriptions.filter(is_trial=True)
        if not trial_sub.exists():
            Subscription.objects.create(
                user=sub.user,
                is_trial=True,
                membership='premium',
                date_start=date,
                date_end=date + relativedelta(months=31)
            )
        else:
            charge_subscription_payment.delay(sub.user.pk)


@shared_task(name="send_subs_warning_email")
def send_subs_email():
    month_date = timezone.now() + relativedelta(months=1)
    two_weeks_date = timezone.now() + relativedelta(weeks=2)
    month_subs = Subscription.objects.filter(
        date_end=month_date.date(), is_active=True, date_end__gt=datetime.date(2020, 12, 1)
    )
    two_weeks_subs = Subscription.objects.filter(
        date_end=two_weeks_date.date(), is_active=True, date_end__gt=datetime.date(2020, 12, 1)
    )
    for sub in month_subs:
        sub.send_month_warning()
    for sub in two_weeks_subs:
        sub.send_two_weeks_warning()
