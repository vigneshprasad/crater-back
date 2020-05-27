from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from community.posts.models import File, Like
from notifications.models import Notification, UserNotification
from users.models import CoverFile


@receiver(pre_save, sender=File)
def post_transcode_file(sender, instance, *args, **kwargs):
    if not instance.file or instance.file.file != instance.object:
        instance.file = CoverFile.objects.create(file=instance.object, user=instance.post.creator)


@receiver(post_save, sender=Like)
def like_notification_post_save(sender, instance,  created, *args, **kwargs):
    if created:
        if instance.post.creator:
            notification = Notification.objects.create(like=instance)
            UserNotification.objects.create(
                user=instance.post.creator, notification=notification
            )
