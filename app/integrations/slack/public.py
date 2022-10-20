from django.conf import settings

from integrations.slack import constants, services


def send_otp_failure_notification(phone_otp_failure):
    """Send OTP failure notification to slack.

    Args:
        phone_otp_failure(PhoneOTPFailure): Phone opt failure object.

    """
    message_text = constants.SLACK_ALERT_FOR_OTP_FAILURE.format(
        failed_otps=phone_otp_failure.generated_since_last_successful,
        last_successful_otp_time=phone_otp_failure.get_display_last_successful_opt_at,
        back_url=settings.BACK_URL
    )
    return services.slack_service.send_message(message_text)
