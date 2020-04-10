from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from community.posts.models import File, Like
from users.models import CoverFile
from notifications.models import Notification, UserNotification

from .serializers import LikeSerializer


@receiver(pre_save, sender=File)
def post_transcode_file(sender, instance, *args, **kwargs):
    if not instance.file or instance.file.file != instance.object:
        instance.file = CoverFile.objects.create(file=instance.object, user=instance.post.creator)


@receiver(post_save, sender=Like)
def like_notification_post_save(sender, instance,  created, *args, **kwargs):
    if created:
        if instance.post.creator:
            send = instance.post.creator.notification_settings.post_likes
            if send:
                data = LikeSerializer(instance).data
                data['obj_type'] = 'like'
                data['obj_pk'] = data['pk']
                data['user'] = str(data['user'])
                try:
                    username = instance.user.name
                except Exception:
                    username = ''
                notification = Notification.objects.create(like=instance)
                UserNotification.objects.create(
                    user=instance.post.creator, notification=notification
                )
                instance.post.creator.send_push(
                    message=_('{username} liked your post').format(username=username),
                    data=data
                )
