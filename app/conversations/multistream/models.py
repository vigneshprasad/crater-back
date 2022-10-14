from django.db import models

from base import models as base_model


class MultiStream(base_model.BaseModel):
    """Squad is a collection of multiple groups
        that can be watched at the same time.

    """
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    # Category of the multistreams.
    category = models.ForeignKey(
        "conversations.Category",
        related_name="squads",
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=True)
    # All streams part of the multistream.
    streams = models.ManyToManyField(
        "conversations.Group",
        related_name="squads",
        blank=True
    )

    def __str__(self):
        return "{} - {}".format(
            self.category,
            ", ".join(
                str(stream.id) for stream in self.streams.all()
            )
        )
