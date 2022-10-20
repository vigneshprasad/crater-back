import datetime

from django.conf import settings

LOGIN_OTP_MESSAGE = "Your login code for Crater club is: {otp}"

TEST_PHONE_NUMBERS = [
    settings.FRESHCHAT_MESSAGING_PHONE_NUMBER,
    "+919111111111",
    "+919222222222",
    "+919333333333",
    "+919444444444",
    "+919555555555",
    "+919666666666"
    "+919777777777",
    "+919888888888"
]

# Adding it here because the settings one is applicable all across the
# app. Only want debug False for crater auth.
DEBUG = False

TEST_OTP = "1111"

MAXIMUM_FAILED_OPT_ATTEMPTS = 10
INCREASING_INTERVAL_FOR_FAILED_OTPS = 10
