from devices import models


def get_device_info_for_user(user):
    """Returns user's device info.

    Args:
        user(User): User object we are getting device info for.

    """
    user_device = models.UserDevice.objects.filter(user=user).first()
    if not (user_device and user_device.device):
        return None

    device = user_device.device

    return {
        "device_name": device.name,
        "device_model": device.model,
        "device_price": device.price
    }
