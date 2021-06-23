from django.dispatch import receiver

from devices import signals
from devices import private


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
