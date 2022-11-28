from django.db.models.signals import post_save
from django.dispatch import receiver

from crater.auth import constants, models, tasks
from integrations.slack import public as slack_public


# @receiver(user_signals.user_created)
def send_welcome_crater_whatsapp(sender, user, *args, **kwargs):
    """Send crater welcome message on user's name population.

    Args:
        sender(User class): User class.
        user(User): User whose name got populated.

    """
    tasks.send_welcome_crater_whatsapp.apply_async(
        args=(user.pk,),
        countdown=120
    )


@receiver(post_save, sender=models.PhoneOtp)
def create_or_update_otp_metric(sender, instance, *args, **kwargs):
    """Create or update Phone otp failure model on PhoneOtp save.

    Args:
        sender(PhoneOtp.__clas__): Class representation of PhoneOtp
        instance(PhoneOtp): Phone OTP that was created or updated.

    """
    failure, _ = models.PhoneOtpMetric.objects.get_or_create()

    if kwargs.get("created"):
        # If a new otp is created, increment generated
        # since value.
        failure.generated_since += 1
        failure.save()
        return

    if instance.is_used():
        failure.last_successful = instance
        # Since this instance of OTP was used, generated since
        # will reset back to zero.
        failure.generated_since = 0
        # Reset the maximum failed attempts once an OTP is
        # successfully used.
        failure.notify_at = constants.MAXIMUM_FAILED_OPT_ATTEMPTS
        failure.last_successful_at = instance.created_at
        failure.save()


@receiver(post_save, sender=models.PhoneOtpMetric)
def send_slack_notification_for_failed_otps(sender, instance, *args, **kwargs):
    """Send failure notification to slack for excessive OTP failures.

    Args:
        sender(PhoneOtpMetric.__clas__): Class representation of PhoneOtp
        instance(PhoneOtpMetric): Phone OTP that was created or updated.

    """
    if instance.generated_since < instance.notify_at:
        return

    # Increase notify limit by a constant interval.
    instance.notify_at += constants.INCREASING_INTERVAL_FOR_FAILED_OTPS
    instance.save()
    # Send Slack notification for the failure.
    slack_public.send_otp_failure_notification(instance)
