from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Comment
from .signals import comment_created_points, comment_created_post_author_points

COMMENT_CREATED_KEY = 5
COMMENT_RECIEVED_POST_AUTHOR_KEY = 4


@receiver(post_save, sender=Comment)
def send_create_comment_points_signal(sender, instance, created, *args, **kwargs):
    if created:
        comment_author = instance.creator
        post_author = instance.post.creator
        if comment_author != post_author:
            if post_author:
                comment_created_post_author_points.send(
                    sender=instance.__class__,
                    user=post_author,
                    rule_key= COMMENT_RECIEVED_POST_AUTHOR_KEY
                )
            if comment_author:
                comment_created_points.send(
                    sender=instance.__class__,
                    user=comment_author,
                    rule_key=COMMENT_CREATED_KEY
                )