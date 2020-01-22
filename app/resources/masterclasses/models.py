from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from notifications.models import Notification, UserNotification
from tags.models import MasterClassTag
from users.models import User
from utils.validators import SizeValidator


class MasterClass(TimeStampedModel):
    author = models.CharField(_('Author Name'), max_length=255)
    position = models.CharField(_('Author Position'), max_length=255)
    description = models.TextField(_('Description'))
    cover = models.FileField(
        upload_to='masterclasses/%Y/%m/%d',
        verbose_name=_('Cover'),
        null=True,
        validators=[SizeValidator(size=512)]
    )
    tags = models.ManyToManyField(MasterClassTag)
    count = models.IntegerField(_('Times viewed'), default=0)

    class Meta:
        verbose_name = _('Master Class')
        verbose_name_plural = _('Master Classes')
        db_table = 'resources_masterclasses'
        ordering = ['-created']

    def __str__(self):
        return self.description


@receiver(post_save, sender=MasterClass)
def master_class_post_save(sender, instance,  created, *args, **kwargs):
    if created:
        notification = Notification.objects.create(master_class=instance)
        users = User.objects.filter(profile__isnull=False)
        for user in users:
            UserNotification.objects.create(user=user, notification=notification)
