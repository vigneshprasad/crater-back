from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from conversations import models as conversation_models
from conversations.group_helpers import models
from utils.socket_io_service import socket_io_service


@receiver(pre_save, sender=models.Viewer)
def post_to_socket_on_count_change(sender, instance, *args, **kwargs):
    """Posts to socket with group_id on change of count.

    Args:
        sender(Viewer.__class__): Class representation of Viewer.
        instance(Viewer): Viewer instance about to be saved.

    """
    if instance._state.adding:
        return

    # Get previous instance for the instance.
    previous_instance = models.Viewer.objects.get(id=instance.id)

    # If the count has changed, send an update to socket with the group_id.
    if instance.count != previous_instance.count:
        socket_io_service.post_viewer_count_update(instance.group_id)


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
