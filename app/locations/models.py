from django.db import models
from django.utils.translation import ugettext_lazy as _


class Country(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name")
    )

    class Meta:
        verbose_name = _("Country")
        verbose_name_plural = _("Countries")
        ordering = ["name"]

    def __str__(self):
        return self.name


class City(models.Model):
    country = models.ForeignKey(
        "locations.Country",
        verbose_name=_("Country"),
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name")
    )
    is_work = models.BooleanField(
        default=False,
        verbose_name=_("Is work")
    )
    order = models.PositiveIntegerField(default=0, blank=False, null=False)

    class Meta:
        verbose_name = _("City")
        verbose_name_plural = _("Cities")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name
