from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from tags.models import MasterClassTag
from utils.validators import SizeValidator


class MasterClass(TimeStampedModel):
    teacher = models.CharField(_('Teacher Name'), max_length=255)
    position = models.CharField(_('Teacher Position'), max_length=255)
    description = models.TextField(_('Description'))
    cover = models.FileField(
        upload_to='masterclasses/%Y/%m/%d',
        verbose_name=_('Cover'),
        null=True,
        validators=[SizeValidator(size=512)]
    )
    tags = models.ManyToManyField(MasterClassTag)

    class Meta:
        verbose_name = _('Master Class')
        verbose_name_plural = _('Master Classes')
        db_table = 'resources_masterclasses'
        ordering = ['-created']

    def __str__(self):
        return self.description
