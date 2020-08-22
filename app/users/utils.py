from allauth.account.models import EmailAddress

from users import signals


def mark_email_as_verified(user):
    """Mark email as verified."""
    email, _ = EmailAddress.objects.get_or_create(
        user=user,
        email=user.email,
        primary=True,
    )
    email.verified = True
    email.save()
    # Sending email confirmation signal.
    signals.email_verified.send(
        sender=user.__class__,
        email_address=email
    )
