from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from conversations import models
from matching import private as matching_private


@receiver(m2m_changed, sender=models.Group.speakers.through)
def update_group_score(sender, instance, *args, **kwargs):
    """Update group score as a user is removed or added to the group."""
    if kwargs.get("action") not in ["post_add", "post_remove"]:
        return

    if not instance.calculate_score:
        return

    speakers = instance.speakers.all()
    score = matching_private.calculate_average_group_score_based_on_user_score(speakers)

    instance.score = score
    instance.save()
