from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Location(models.Model):
    """
    User's community group location
    """
    name = models.CharField(_('City Name'), max_length=255)
    icon = models.ImageField(
        upload_to='locations/icons/%Y/%m/%d/',
        verbose_name=_('Location Icon'),
        null=True
    )
    order = models.PositiveIntegerField(default=0, blank=False, null=False)

    class Meta:
        verbose_name = _('Community Location')
        verbose_name_plural = _('Community Locations')
        db_table = 'community_locations'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Group(models.Model):
    """
    User's community group
    """
    name = models.CharField(_('Name'), max_length=255)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='groups')
    cover = models.ImageField(
        upload_to='groups/cover/%Y/%m/%d/',
        verbose_name=_('Cover Image'),
        null=True
    )
    icon = models.ImageField(
        upload_to='groups/icons/%Y/%m/%d/',
        verbose_name=_('Group Icon'),
        null=True
    )

    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')
        db_table = 'community_groups'

    def __str__(self):
        return self.name


class UserRequest(models.Model):
    """
    User's community group relation (requests)
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='user_groups')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_users')
    is_approved = models.BooleanField(_('Approved'), default=False)

    class Meta:
        verbose_name = _('User Request')
        verbose_name_plural = _('User Requests')
        db_table = 'user_requests'
        unique_together = ('user', 'group')


class Following(models.Model):
    """
    User's followers
    """
    followed = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='follows')
    follower = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='followers')

    class Meta:
        verbose_name = _('Follow')
        verbose_name_plural = _('Follows')
        db_table = 'user_followers'
        unique_together = ('followed', 'follower')


class Block(models.Model):
    """
    User's blockers
    """
    blocked = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='blocks')
    blocker = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='blockers')

    class Meta:
        verbose_name = _('Blocker')
        verbose_name_plural = _('Blockers')
        db_table = 'user_blockers'
        unique_together = ('blocked', 'blocker')
