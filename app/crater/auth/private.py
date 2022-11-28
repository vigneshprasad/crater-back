import random as r

from crater.auth import constants


def generate_otp(phone_number):
    """Generates a random 4 digit OTP."""
    otp = ""
    if constants.DEBUG or phone_number in constants.TEST_PHONE_NUMBERS:
        return constants.TEST_OTP

    for i in range(4):
        otp += str(r.randint(0, 9))

    return otp
