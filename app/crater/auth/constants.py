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


HACK_2_SKILL_GROUP = "hack2skill-user"
HACK_2_SKILL_SOURCE = "H2Skill"
