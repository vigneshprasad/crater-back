from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from tags.models import MasterClassTag
from utils.validators import SizeValidator


class MasterClass(TimeStampedModel):
    author = models.CharField(_('Author Name'), max_length=255)
    position = models.CharField(_('Author Position'), max_length=255)
    description = models.TextField(_('Description'))
    cover = models.FileField(
        upload_to='masterclasses/%Y/%m/%d',
        verbose_name=_('Video'),
        null=True,
        validators=[SizeValidator(size=512)]
    )
    file = models.OneToOneField(
        'users.CoverFile',
        null=True,
        verbose_name=_('Cover File'),
        related_name='masterclasses',
        on_delete=models.SET_NULL
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
