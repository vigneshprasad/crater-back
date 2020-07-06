from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .signals import profile_completed, referal_success_points_signal, user_signed_up, user_updated

PROFILE_COMPLETED_POINTS_KEY = 1
REFERAL_SUCCESS_POINTS_KEY = 13

User = get_user_model()


@receiver(post_save, sender=User)
def send_profile_completed_points_signal(sender, instance, created, *args, **kwargs):
    user_updated.send(
        sender=instance.__class__,
        user=instance,
    )
    
    if created:    
        user_signed_up.send(
            sender=instance.__class__,
            user=instance
        )

    if instance.profile_completed:
        points_log = instance.points_log
        if not points_log.filter(action__key=PROFILE_COMPLETED_POINTS_KEY).exists():
            profile_completed.send(
                sender=instance.__class__,
                rule_key=PROFILE_COMPLETED_POINTS_KEY,
                user=instance
            )
        if instance.referer:
            referer_points_log = instance.referer.points_log
            if not referer_points_log.filter(action__key=REFERAL_SUCCESS_POINTS_KEY).exists():
                referal_success_points_signal.send(
                    sender=instance.referer.__class__,
                    user=instance.referer,
                    rule_key=REFERAL_SUCCESS_POINTS_KEY
                )
