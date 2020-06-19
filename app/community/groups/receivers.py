from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Following
from .signals import follower_recieved_signal

NEW_FOLLOWER_POINTS_KEY = 7


@receiver(post_save, sender=Following)
def send_following_points_signal(sender, instance, created, *args, **kwargs):
  if created:
    follower_recieved_signal.send(
      sender=instance.followed.__class__,
      user=instance.followed,
      rule_key=NEW_FOLLOWER_POINTS_KEY
    )


@receiver(post_delete, sender=Following)
def send_follower_removed_signal(sender, instance, *args, **kwargs):
  follower_recieved_signal.send(
    sender=instance.followed.__class__,
    user=instance.followed,
    rule_key=NEW_FOLLOWER_POINTS_KEY,
    base_factor=-1
  )