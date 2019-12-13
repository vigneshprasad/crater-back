from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from community.posts.models import Post
from resources.events.models import Event


class Comment(TimeStampedModel):
    """
    User's post in community chat
    """
    message = models.TextField(_('Comment Message'))
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', null=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_comments', null=True)
    creator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')
        db_table = 'community_comments'
        ordering = ['-created']
