import datetime

from django.dispatch import receiver

from devices import signals
from devices import private
from users import signals as user_signals


@receiver(signals.new_user_device_detected)
def create_or_update_user_device(
        sender,
        user,
        device_name,
        device_model,
        device_price,
        *args,
        **kwargs
):
    """Creates or update user device on new user device
        detected for user.

    Args:
        sender(class): User class.
        user(User): User whose info has to be added or updated.
        device_name(str): Name of the device the user is using.
        device_model(str): Model number of the user's device.
        device_price(int): Price of the device.

    """
    private.create_or_update_user_device(
        user,
        device_name,
        device_model,
        device_price
    )


@receiver(user_signals.profile_requested)
def update_device_last_used(
        sender,
        profile,
        *args,
        **kwargs
):
    """Updates last used device for a user on profile request
        from client.

    Args:
        sender(class): Profile class.
        profile(Profile): Profile of the user who requested for profile.

    """
    user = profile.user
    user_device = private.get_user_device(user)

    if not user_device:
        return

    user_device.last_used = datetime.datetime.now()
    user_device.save()
