from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from base.models import BaseModel


class UserPoints(BaseModel):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='points'
    )
    points = models.IntegerField(default=0)

    class Meta:
        verbose_name = _('User Points')
        verbose_name_plural = _('User Points')

    def __str__(self):
        return self.user.name


class PointsRule(BaseModel):
    key = models.IntegerField(unique=True)
    desc = models.CharField(max_length=120)
    points_value = models.IntegerField()

    def __str__(self):
        return f"Points Rule ({self.desc})"


class PointsLog(BaseModel):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='points_log'
    )
    action = models.ForeignKey(
        PointsRule,
        on_delete=models.DO_NOTHING,
        related_name='rule'
    )
    base_points_value = models.IntegerField(_("Base Points"), null=True)
    base_factor = models.IntegerField(_("Base Factor"), default=1)
    bonus_points_value = models.IntegerField(_("Bonus Points"), null=True)
    bonus_factor = models.IntegerField(_("Bonus Factor"), default=1)

    def __str__(self):
        return f"{self.user.name} ({self.base_points_value})"
