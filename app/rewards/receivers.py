from django.dispatch import receiver
from django.db.models.signals import post_save

from rewards import models
from rewards.signals import package_request_created


@receiver(post_save, sender=models.PackageRequest)
def apply_points_post_package_creation(sender, instance, created, *args, **kwargs):
    if not created:
        return

    package_request_created.send(
        sender=instance,
        user=instance.requested_by,
        points_applied=instance.point_applied,
    )
