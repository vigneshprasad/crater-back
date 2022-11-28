from django.conf import settings

from integrations.slack import constants, services


def send_otp_failure_notification(phone_otp_metric):
    """Send OTP failure notification to slack.

    Args:
        phone_otp_metric(PhoneOtpMetric): Phone opt failure object.

    """
    message_text = constants.SLACK_ALERT_FOR_OTP_FAILURE.format(
        failed_otps=phone_otp_metric.generated_since,
        last_successful_otp_time=phone_otp_metric.get_display_last_successful_at(),
        back_url=settings.BACK_URL
    )
    return services.slack_service.send_message(message_text)


def send_login_failure_notification(phone_number, users):
    """Sends notification for login failure by a phone number

    Args:
        phone_number(str): Phone number user is trying to
            log in/signup from.
        users(queryset.User): All users with the same phone
            number on backend.

    """
    message_text = constants.SLACK_ALERT_FOR_LOGIN_FAILURE.format(
        phone_number=phone_number,
        total_users=users.count(),
        back_url=settings.BACK_URL
    )
    return services.slack_service.send_message(message_text)


def send_twilio_account_failure_notification(sms):
    """Sends notification for Twilio account failure notification.

    Args:
        sms(SMS): SMS which returned the failure error.

    """
    message_text = constants.SLACK_ALERT_FOR_TWILIO_ACCOUNT_FAILURE.format(
        error_code=sms.error_code,
        error_message=sms.error_message,
        back_url=settings.BACK_URL
    )
    return services.slack_service.send_message(message_text)
