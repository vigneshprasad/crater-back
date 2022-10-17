from django.db import models
from django.utils.translation import ugettext_lazy as _

from base import models as base_models


class Viewer(base_models.BaseModel):

    group = models.OneToOneField(
        "conversations.Group",
        on_delete=models.CASCADE
    )
    count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Group Helper")
        verbose_name_plural = _("User Interests")
        ordering = ["-created_at"]

    def __str__(self):
        return "{} - {}".format(self.group.id, self.count)
