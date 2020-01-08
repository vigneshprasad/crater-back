from django.db import models
from django.utils.translation import ugettext_lazy as _


class ExchangeCategory(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active')
    )

    class Meta:
        verbose_name_plural = _('Exchange Categories')
        verbose_name = _('Exchange Category')
        ordering = ['is_active', 'name']

