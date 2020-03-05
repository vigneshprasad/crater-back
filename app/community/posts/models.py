from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from community.groups.models import Group
from notifications.models import Notification, UserNotification
from users.models import User
from utils.validators import SizeValidator


class Post(TimeStampedModel):
    """
    User's post in community chat
    """
    message = models.TextField(_('Post Message'))
    creator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')
        db_table = 'community_posts'
        ordering = ('-created',)

    def __str__(self):
        return self.message


class File(models.Model):
    """
    File attached to post
    """
    object = models.FileField(
        _('File'),
        upload_to='posts/%Y/%m/%d',
        validators=[SizeValidator(size=512)]
    )
    file = models.OneToOneField(
        'users.CoverFile',
        null=True,
        verbose_name=_('Cover File'),
        related_name='post_files',
        on_delete=models.SET_NULL
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='files')

    class Meta:
        verbose_name = _('File')
        verbose_name_plural = _('Files')
        db_table = 'community_files'


class Like(models.Model):
    """
    User likes for posts
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='user_likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        verbose_name = _('Like')
        verbose_name_plural = _('Likes')
        db_table = 'post_likes'
        unique_together = ['user', 'post']


class Report(TimeStampedModel):
    """
    Report a post for obscene content
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='user_reports')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    is_reviewed = models.BooleanField(_('Reviewed'), default=False)

    class Meta:
        verbose_name = _('Reported Post')
        verbose_name_plural = _('Reports')
        db_table = 'post report'
        unique_together = ['user', 'post']


@receiver(post_save, sender=Post)
def post_post_save(sender, instance,  created, *args, **kwargs):
    if created:
        notification = Notification.objects.create(post=instance)
        users = User.objects.filter(profile__isnull=False)
        users.exclude(pk=instance.creator.pk)
        if instance.group:
            users_approved = list(instance.group.group_users.filter(is_approved=True).values_list('user_id', flat=True))
            users = User.objects.filter(pk__in=users_approved)
        users = users.exclude(pk=instance.creator.pk)
        for user in users:
            UserNotification.objects.create(user=user, notification=notification)


@receiver(post_save, sender=Like)
def like_notification_post_save(sender, instance,  created, *args, **kwargs):
    if created:
        if instance.post.creator:
            send = instance.post.creator.notification_settings.post_likes
            if send:
                from .serializers import LikeSerializer
                data = LikeSerializer(instance).data
                data['obj_type'] = 'like'
                data['obj_pk'] = data['pk']
                try:
                    username = instance.user.profile.name
                except Exception:
                    username = ''
                instance.post.creator.send_push(
                    message=_('{username} liked your post').format(username=username),
                    data=data
                )
