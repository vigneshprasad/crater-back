from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel


class UserNotificationsSettings(models.Model):
    user = models.OneToOneField(
        'users.User',
        related_name='notification_settings',
        on_delete=models.CASCADE,
        verbose_name=_('User')
    )
    messages = models.BooleanField(
        default=True
    )
    post_comments = models.BooleanField(
        default=True
    )
    post_likes = models.BooleanField(
        default=True
    )
    new_videos_posted = models.BooleanField(
        default=True
    )
    new_articles_posted = models.BooleanField(
        default=True
    )
    new_events_created = models.BooleanField(
        default=True
    )


class Notification(TimeStampedModel):
    post = models.ForeignKey(
        'posts.Post',
        related_name='notifications',
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_('Post')
    )
    comment = models.ForeignKey(
        'comments.Comment',
        related_name='notifications',
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_('Comment')
    )
    event = models.ForeignKey(
        'events.Event',
        related_name='notifications',
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_('Event')
    )
    article = models.ForeignKey(
        'curated_articles.CuratedArticle',
        verbose_name=_('Article'),
        on_delete=models.CASCADE,
        null=True,
        related_name='notifications'
    )
    master_class = models.ForeignKey(
        'masterclasses.MasterClass',
        verbose_name=_('Master Class'),
        on_delete=models.CASCADE,
        null=True,
        related_name='notifications'
    )
    PUSH_PERMISSION_DICT = {
        'event': 'new_events_created',
        'article': 'new_articles_posted',
        'master_class': 'new_videos_posted',
        'comment': 'post_comments'
    }
    PUSH_MESSAGE_DICT = {
        'event': _('New event posted'),
        'article': _('New article posted'),
        'master_class': _('New master class posted'),
        'comment': _('New comment posted')
    }

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')

    @property
    def obj_type(self):
        if self.post:
            return 'post'
        elif self.comment:
            return 'comment'
        elif self.event:
            return 'event'
        elif self.article:
            return 'article'
        elif self.master_class:
            return 'master_class'
        return None

    @property
    def text(self):
        if not self.obj_type:
            return None
        text_data = {
            'post': 'post.message',
            'comment': 'comment.message',
            'event': 'event.text',
            'article': 'article.text',
            'master_class': 'master_class.description'
        }
        return getattr(self, text_data.get(self.obj_type))

    @property
    def author_name(self):
        if not self.obj_type:
            return None
        name_data = {
            'post': 'post.creator.name',
            'comment': 'comment.creator.name',
            'event': 'event.title',
            'article': 'article.website_tag.name',
            'master_class': 'master_class.author'
        }
        return getattr(self, name_data.get(self.obj_type))

    @property
    def author_avatar(self):
        if not self.obj_type:
            return None
        avatar_data = {
            'post': 'post.creator.profile.photo',
            'comment': 'comment.creator.profile.photo',
            'event': 'event.picture',
            'article': 'article.picture',
            'master_class': 'master_class.cover'
        }
        return getattr(self, avatar_data.get(self.obj_type))

    @property
    def obj_pk(self):
        if not self.obj_type:
            return None
        pk_data = {
            'post': 'post.pk',
            'comment': 'comment.pk',
            'event': 'event.pk',
            'article': 'article.pk',
            'master_class': 'master_class.pk'
        }
        return getattr(self, pk_data.get(self.obj_type))

    def message(self):
        if not self.obj_type:
            return ''
        return self.PUSH_MESSAGE_DICT.get(self.obj_type, 'None message')


class UserNotification(TimeStampedModel):
    user = models.ForeignKey(
        'users.User',
        related_name='notifications',
        verbose_name=_('User'),
        on_delete=models.CASCADE
    )
    notification = models.ForeignKey(
        'notifications.Notification',
        related_name='users_notification',
        verbose_name=_('Notification'),
        on_delete=models.CASCADE
    )
    is_read = models.BooleanField(
        default=False
    )

    class Meta:
        verbose_name_plural = _('User Notifications')
        verbose_name = _('User Notification')
        ordering = ['-created']


@receiver(post_save, sender=UserNotification)
def user_notification_post_save(sender, instance,  created, *args, **kwargs):
    if created:
        if instance.notification.obj_type in instance.notification.PUSH_PERMISSION_DICT.keys():
            send = getattr(
                instance.user.notification_settings,
                instance.notification.PUSH_PERMISSION_DICT.get(instance.notification.obj_type)
            )
        else:
            send = True
        if send:
            from .serializers import PushNotificationSerializer
            data = PushNotificationSerializer(instance).data
            instance.user.send_push(
                message=instance.notification.message(),
                data=data
            )
