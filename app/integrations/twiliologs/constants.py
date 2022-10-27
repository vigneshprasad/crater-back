from django.conf import settings

# Default login OTP message for Crater.
LOGIN_OTP_MESSAGE = "Your login code for Crater club is: {otp}"

# Callback url for SMS status update call backs.
SMS_CALLBACK_URL = settings.BACK_URL + "/v1/integrations/twilio/status/"

# All Twilio status codes.
SMS_STATUS_QUEUED = "queued"
SMS_STATUS_FAILED = "failed"
SMS_STATUS_SENT = "sent"
SMS_STATUS_DELIVERED = "delivered"
SMS_STATUS_UNDELIVERED = "undelivered"

# Status that denotes an SMS success.
SMS_SUCCESSFUL_STATUS = [SMS_STATUS_DELIVERED]

# Status that denotes an SMS failure.
SMS_FAILURE_STATUS = [
    SMS_STATUS_UNDELIVERED,
    SMS_STATUS_FAILED
]

# Error codes from Twilio for which to
# alert admins.
TWILIO_ALERT_CODES = [
    "30002"
]
