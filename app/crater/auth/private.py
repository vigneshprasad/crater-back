import random as r


def generate_otp():
    """Generates a random 4 digit OTP."""
    otp = ""
    for i in range(4):
        otp += str(r.randint(0, 9))

    return otp
