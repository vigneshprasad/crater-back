from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from conversations import models as conversation_models
from conversations.group_helpers import models
from utils.socket_io_service import socket_io_service


@receiver(post_save, sender=conversation_models.Group)
def create_viewer_on_group_creation(sender, instance, *args, **kwargs):
    """Creates a viewer instance on group creation.

    Args:
        sender(Group.__class__): Class representation of Group.
        instance(Group): Group that was created.

    """
    if not kwargs.get("created"):
        return False

    # Create viewer is group is created.
    models.Viewer.objects.create(group=instance)


@receiver(post_save, sender=models.Viewer)
def post_to_socket_on_count_change_post(sender, instance, *args, **kwargs):
    if kwargs.get("created"):
        return

    socket_io_service.post_viewer_count_update(instance.group_id)
