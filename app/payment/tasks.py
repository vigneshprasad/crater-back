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
