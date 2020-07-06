from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Post, Like
from .signals import (
    post_created,
    points_like_received_on_post,
    points_liked_post
)

CREATE_POST_POINTS_KEY = 2
RECEIVED_LIKE_ON_POST_KEY = 3
LIKED_POST_KEY = 6


@receiver(post_save, sender=Post)
def send_post_created_points_signal(sender, instance, created, *args, **kwargs):
    if created:
        post_created.send(
            sender=instance.__class__,
            user=instance.creator,
            rule_key=CREATE_POST_POINTS_KEY,
            base_factor=1,
            post=instance
        )


@receiver(post_delete, sender=Post)
def send_post_deleted_points_signal(sender, instance, *args, **kwargs):
    if instance.creator and instance.creator.has_points:
        post_created.send(
            sender=instance.__class__,
            user=instance.creator,
            rule_key=CREATE_POST_POINTS_KEY,
            base_factor=-1
        )


@receiver(post_save, sender=Like)
def send_like_points_signal(sender, instance, created, *args, **kwargs):
    if created:
        like_creator = instance.user
        post_creator = instance.post.creator
        if post_creator != like_creator:
            if post_creator:
                points_like_received_on_post.send(
                    sender=post_creator.__class__,
                    user=post_creator,
                    rule_key=RECEIVED_LIKE_ON_POST_KEY,
                    base_factor=1
                )
            if like_creator:
                points_liked_post.send(
                    sender=like_creator.__class__,
                    user=like_creator,
                    rule_key=LIKED_POST_KEY
                )


@receiver(post_delete, sender=Like)
def send_delete_like_points_signal(sender, instance, *args, **kwargs):
    like_creator = instance.user
    post_creator = instance.post.creator
    if post_creator != like_creator:
        if post_creator and post_creator.has_points:
            points_like_received_on_post.send(
                sender=post_creator.__class__,
                user=post_creator,
                rule_key=RECEIVED_LIKE_ON_POST_KEY,
                base_factor=-1
            )
        if like_creator and like_creator.has_points:
            points_liked_post.send(
                sender=like_creator.__class__,
                user=like_creator,
                rule_key=LIKED_POST_KEY,
                base_factor=-1
            )