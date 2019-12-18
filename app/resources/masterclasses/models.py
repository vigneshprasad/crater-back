from django.db import models
from django.utils.translation import ugettext_lazy as _

from utils.validators import SizeValidator


class Masterclass(models.Model):
    cover = models.FileField(
        upload_to='masterclasses/%Y/%m/%d',
        verbose_name=_('Cover'),
        null=True,
        validators=[SizeValidator(size=512)]
    )

    class Meta:
        verbose_name = _('Masterclass')
        verbose_name_plural = _('Masterclasses')
        db_table = 'resources_masterclasses'

    def __str__(self):
        return self.title
