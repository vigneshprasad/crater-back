from django.db.models.signals import post_save
from django.dispatch import receiver

from crater.auth import tasks
from crater.auth import models, constants
from users import signals as user_signals
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
def create_or_update_failure(sender, instance, *args, **kwargs):
    """Create or update Phone otp failure model on PhoneOtp save.

    Args:
        sender(PhoneOtp.__clas__): Class representation of PhoneOtp
        instance(PhoneOtp): Phone OTP that was created or updated.

    """
    failure, _ = models.PhoneOTPFailure.objects.get_or_create()
    if kwargs.get("created"):
        # If a new otp is created, add 1 to generated
        # since last successful OTP.
        failure.generated_since_last_successful += 1
        failure.save()
        return

    if instance.used and instance.user:
        failure.last_successful_otp = instance
        failure.generated_since_last_successful = 0
        # Reset the maximum failed attempts once an OTP is
        # successfully used.
        failure.maximum_opt_failures_allowed = constants.MAXIMUM_FAILED_OPT_ATTEMPTS
        failure.last_successful_otp_at = instance.created_at
        failure.save()


@receiver(post_save, sender=models.PhoneOTPFailure)
def send_slack_notification_for_excessive_failures(sender, instance, *args, **kwargs):
    """Send failure notification to slack for excessive OTP failures.

    Args:
        sender(PhoneOTPFailure.__clas__): Class representation of PhoneOtp
        instance(PhoneOTPFailure): Phone OTP that was created or updated.

    """
    if instance.generated_since_last_successful < instance.maximum_opt_failures_allowed:
        return

    slack_public.send_otp_failure_notification(instance)
    instance.maximum_opt_failures_allowed += constants.MAXIMUM_FAILED_OPT_ATTEMPTS
    instance.save()
