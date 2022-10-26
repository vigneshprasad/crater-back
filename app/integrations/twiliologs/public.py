from integrations.twiliologs import constants, models, services


def send_opt_sms_for_login(phone_otp):
    """Sends SMS for login to Crater.

    Args:
        phone_otp(PhoneOtp): Phone OTP object.

    """
    message_text = constants.LOGIN_OTP_MESSAGE.format(
        otp=phone_otp.otp
    )
    message_data = services.twilio_service.send_message(
        phone_otp.get_phone_number(),
        message_text
    )
    if not message_data:
        return

    # Create a log for message sent on our backend.
    sms, _ = models.SMS.objects.get_or_create(
        phone_otp=phone_otp,
        defaults={
            "status": message_data.status,
            "error_code": message_data.error_code,
            "sid": message_data.sid
        }
    )

    return sms
