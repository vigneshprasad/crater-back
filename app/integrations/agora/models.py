from django.db import models

from django.utils.translation import ugettext_lazy as _

from integrations.agora import constants
from base import models as base_models


class AgoraRTCInfo(base_models.BaseModel):

    class ChannelType(models.IntegerChoices):
        GROUP = 0, _(constants.CHANNEL_TYPE_GROUP)
        ONE_ON_ONE = 1, _(constants.CHANNEL_TYPE_ONE_ON_ONE)

    type = models.IntegerField(
        choices=ChannelType.choices,
        default=ChannelType.GROUP,
    )
    channel_id = models.IntegerField()
    channel_name = models.CharField(
        max_length=128,
    )
