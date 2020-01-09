from django.db.models.signals import post_save
from django.dispatch import receiver

from community.comments.models import Comment


@receiver(post_save, sender=Comment)
def update_post(sender, instance, **kwargs):
    if instance.post:
        instance.post.save()
