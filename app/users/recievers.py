import datetime
import logging

from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from notifications import signals as notification_signals
from users import choices
from users import services
from users import signals
from users import models


PROFILE_COMPLETED_POINTS_KEY = 1
REFERAL_SUCCESS_POINTS_KEY = 13

User = get_user_model()


@receiver(pre_save, sender=get_user_model())
def create_push_and_rent(sender, instance, *args, **kwargs):
    if not instance.name:
        instance.name = f'{instance.first_name} {instance.last_name}'
    return instance


@receiver(post_save, sender=get_user_model())
def set_referrer_relation(sender, instance, *args, **kwargs):
    if instance.referer:
        models.Referral.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def send_profile_completed_points_signal(sender, instance, created, *args, **kwargs):
    signals.user_updated.send(
        sender=instance.__class__,
        user=instance,
    )
    
    if created:
        signals.user_signed_up.send(
            sender=instance.__class__,
            user=instance
        )

    if instance.profile_completed:
        points_log = instance.points_log
        if not points_log.filter(action__key=PROFILE_COMPLETED_POINTS_KEY).exists():
            signals.profile_completed.send(
                sender=instance.__class__,
                rule_key=PROFILE_COMPLETED_POINTS_KEY,
                user=instance
            )
        if instance.referer:
            referer_points_log = instance.referer.points_log
            if not referer_points_log.filter(action__key=REFERAL_SUCCESS_POINTS_KEY).exists():
                signals.referal_success_points_signal.send(
                    sender=instance.referer.__class__,
                    user=instance.referer,
                    rule_key=REFERAL_SUCCESS_POINTS_KEY
                )


@receiver(signals.profile_requested)
def update_user_activity(sender, profile, **kwargs):
    """Updates user activity on every profile retrieve call.

    Args:
        sender(Profile class): Class value of the profile model.
        profile(Profile): Profile object of the user that made the
            request.

    """
    user_activity, created = models.UserActivity.objects.update_or_create(
        user=profile.user,
        defaults={
            "last_active": datetime.datetime.now()
        }
    )

    return created
c