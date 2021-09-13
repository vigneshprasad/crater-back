from allauth.account import models as account_models

from users import signals
from users import tasks


def mark_email_as_verified(user):
    """Mark email as verified.

    Args:
        user(User): User object whose email is being verified.

    """
    email, _ = account_models.EmailAddress.objects.get_or_create(
        user=user,
        email=user.email,
        primary=True
    )

    # If email is already verified, no need to do anything.
    if email.verified:
        return True

    email.verified = True
    email.save()

    # Sending email confirmation signal.
    signals.email_verified.send(
        sender=user.__class__,
        email_address=email
    )
    return True


def send_sms(phone_number, message):
    """Send sms to a phone number.

    Args:
        phone_number(str): Phone number we are sending the
            message to.
        message(str): Message we are seding in the text.

    """
    tasks.send_twilio_message.delay(str(phone_number), message)
