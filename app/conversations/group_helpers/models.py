from django.db import models
from django.utils.translation import ugettext_lazy as _

from base import models as base_models
from utils.socket_io_service import socket_io_service


class Viewer(base_models.BaseModel):

    group = models.OneToOneField(
        "conversations.Group",
        on_delete=models.CASCADE
    )
    count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Group Helper")
        verbose_name_plural = _("Group Helpers")
        ordering = ["-created_at"]

    def __str__(self):
        return "{} - {}".format(self.group.id, self.count)

    def increment(self):
        self.count += 1
        self.save()
        socket_io_service.post_viewer_count_update(self.group_id)

    def decrement(self):
        self.count -= 1
        self.save()
        socket_io_service.post_viewer_count_update(self.group_id)
