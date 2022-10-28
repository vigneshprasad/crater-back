from django.db.models.signals import post_save
from django.dispatch import receiver

from integrations.twiliologs import constants, models
from integrations.slack import public as slack_public


@receiver(post_save, sender=models.SMS)
def update_phone_otp_status(sender, instance, *args, **kwargs):
    """Update phone otp status on SMSLog status update.

    Args:
        sender(SMSLog.__class__): Class representation of SMSLog
        instance(SMSLog): SMS log that was updated.

    """
    if instance.status not in constants.SMS_SUCCESSFUL_STATUS:
        return

    # If the SMS is successfully delivered, mark opt successful.
    phone_otp = instance.phone_otp
    phone_otp.mark_successful()


@receiver(post_save, sender=models.SMS)
def send_alert_is_account_suspended(sender, instance, *args, **kwargs):
    """Send alert if we get account suspension error code from Twilio.

    Args:
        sender(SMSLog.__class__): Class representation of SMSLog
        instance(SMSLog): SMS log that was updated.

    """
    if instance.status not in constants.SMS_FAILURE_STATUS:
        return

    if instance.error_code not in constants.TWILIO_ALERT_CODES:
        return

    slack_public.send_twilio_account_failure_notification(instance)
