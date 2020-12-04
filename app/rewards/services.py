from rewards import models


def get_max_rewards_rs_conversion():
    """

    Returns: (int) max rs conversion factor for all packages

    """

    packages = models.Package.objects.filter(is_active=True)
    max_conversion = 0
    for package in packages:
        if package.points_conversion > max_conversion:
            max_conversion = package.points_conversion

    return int(max_conversion)
