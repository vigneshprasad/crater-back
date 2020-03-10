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
        'event': _('You have been invited to an event'),
        'article': _('A new article has been shared'),
        'master_class': _('A new video has been shared'),
        'comment': _('{username} commented on your post')
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
            'post': self.post.message if self.post else None,
            'comment': self.comment.message if self.comment else None,
            'event': self.event.title if self.event else None,
            'article': self.article.title if self.article else None,
            'master_class': self.master_class.description if self.master_class else None
        }
        return text_data.get(self.obj_type, None)

    @property
    def author_name(self):
        if not self.obj_type:
            return None
        name_data = {
            'post': self.post.creator.name if self.post else None,
            'comment': self.comment.creator.name if self.comment else None,
            'event': self.event.title if self.event else None,
            'article': self.article.website_tag.name if self.article else None,
            'master_class': self.master_class.author if self.master_class else None
        }
        return name_data.get(self.obj_type, None)

    @property
    def author_avatar(self):
        if not self.obj_type:
            return None
        avatar_data = {
            'post': self.post.creator.profile.photo if self.post else None,
            'comment': self.comment.creator.profile.photo if self.comment else None,
            'event': self.event.picture if self.event else None,
            'article': self.article.picture if self.article else None,
            'master_class': self.master_class.cover if self.master_class else None
        }
        return avatar_data.get(self.obj_type, None)

    @property
    def obj_pk(self):
        if not self.obj_type:
            return None
        pk_data = {
            'post': self.post_id if self.post else None,
            'comment': self.comment.post_id if self.comment else None,
            'event': self.event_id if self.event else None,
            'article': self.article_id if self.article else None,
            'master_class': self.master_class_id if self.master_class else None
        }
        return pk_data.get(self.obj_type, None)

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
            send = False
        if send:
            from .serializers import PushNotificationSerializer
            data = PushNotificationSerializer(instance).data
            try:
                username = instance.notification.comment.creator.name
            except Exception:
                username = ''
            instance.user.send_push(
                message=instance.notification.message().format(username=username),
                data=data
            )
