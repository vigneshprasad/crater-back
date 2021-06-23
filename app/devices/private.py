from django.utils import timezone

from devices import models


def get_or_create_device(device_name, device_model, device_price):
    """Gets or creates a device entry for provided details.

    Args:
        device_name(str): Name of the device.
        device_model(str): Model of the device.
        device_price(int): Price of the device.

    Note:
        If the device is not found it creates a new
            device for the details.

    """
    if not (device_name or device_model):
        return None

    try:
        device = models.Device.objects.get(
            name=device_name.lower(),
            model=device_model.lower(),
            price=device_price
        )
    except models.Device.DoesNotExist:
        device = create_or_update_device(
            device_name,
            device_model,
            device_price
        )

    return device


def create_or_update_device(device_name, device_model, device_price):
    """Creates a device entry for provided details.

    Args:
        device_name(str): Name of the device.
        device_model(str): Model of the device.
        device_price(int): Price of the device.

    Note:
        It won't create duplicates in case device is already
            present. It updates the price of the device in
            that case.

    """
    device, created = models.Device.objects.update_or_create(
        name=device_name.lower(),
        model=device_model.lower(),
        defaults={
            "price": device_price
        }
    )

    return device


def create_or_update_user_device(
        user,
        device_name,
        device_model,
        device_price
):
    """
    Create or update the User's devices based on the args.

    Args:
        user(User): User whose info has to be added or updated.
        device_name(str): Name of the device the user is using.
        device_model(str): Model number of the user's device.
        device_price(int): Price of the device.

    Return:
        user_Device(UserDevice): UserDevice object, created or updated.

    """

    # This will always give you a device.
    device = get_or_create_device(device_name, device_model, device_price)

    if not device:
        return None

    user_device, created = models.UserDevice.objects.update_or_create(
        user=user,
        device=device,
        defaults={"last_used": timezone.now()}
    )

    return user_device
