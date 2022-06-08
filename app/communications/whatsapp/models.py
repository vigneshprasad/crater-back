from django.db import models

# Create your models here.
from base import models as base_models
from communications.whatsapp import constants


class WhatsappProvider(base_models.BaseModel):

    WHATSAPP_PROVIDER_CHOICES = (
        (constants.FRESHCHAT_WHATSAPP_PROVIDER_ENUM, constants.FRESHCHAT_WHATSAPP_PROVIDER),
        (constants.WATI_9501_WHATSAPP_PROVIDER_ENUM, constants.WATI_9501_WHATSAPP_PROVIDER),
        (constants.WATI_8953_WHATSAPP_PROVIDER_ENUM, constants.WATI_8953_WHATSAPP_PROVIDER)
    )

    MESSAGE_TYPES = (
        (constants.CRATER_WELCOME_MESSAGE, constants.CRATER_WELCOME_MESSAGE),
        (constants.REMINDER_FOR_STREAM_ATTENDEES, constants.REMINDER_FOR_STREAM_ATTENDEES),
        (constants.REMINDER_FOR_STREAM_FOLLOWERS, constants.REMINDER_FOR_STREAM_FOLLOWERS),
        (constants.REMINDER_FOR_STREAM_CREATOR, constants.REMINDER_FOR_STREAM_CREATOR)
    )

    message_type = models.CharField(max_length=132, choices=MESSAGE_TYPES)
    provider = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=WHATSAPP_PROVIDER_CHOICES
    )
