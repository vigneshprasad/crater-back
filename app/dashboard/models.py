from django.db import models
from django.utils.translation import ugettext_lazy as _


class Dashboard(models.Model):
    proxy = True

    class Meta:
        verbose_name = _('Dashboard')
        verbose_name_plural = _('Dashboard')
        db_table = 'dashboard'
