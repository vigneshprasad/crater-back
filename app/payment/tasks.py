from __future__ import absolute_import, unicode_literals

from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from utils.stripe_service import stripe_service
from .models import Subscription


@shared_task(name='charge_subscription_payment')
def charge_subscription_payment(self, user_pk):
    from users.models import User
    try:
        user = User.objects.get(pk=user_pk)
        date = timezone.now().date()
        if not user.has_active_subscription:
            customer_id = None
            if hasattr(user, 'bank_details') and user.bank_details:
                customer_id = user.bank_details.stripe_customer_id
            if customer_id:
                charge = None
                try:
                    charge = stripe_service.create_customer_charge(
                        customer_id=customer_id,
                        amount=350,
                        description='New Subscription payment'
                    )
                except:
                    pass
                if charge and charge.paid:
                    Subscription.objects.create(
                        user=user,
                        date_start=date,
                        date_end=date + relativedelta(years=1)
                    )
    except User.DoesNotExist:
        pass


@shared_task(name="check_subscription")
def check_subscription(self):
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
        else:
            charge_subscription_payment.delay(sub.user.pk)


