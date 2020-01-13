from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from community.groups.models import Group
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


class Report(models.Model):
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
