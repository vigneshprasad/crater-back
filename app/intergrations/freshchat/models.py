from django.db import models
from django.utils.translation import ugettext_lazy as _

from base import models as base_models
from users import models as user_models


class FreshChatUser(base_models.BaseModel):
    user = models.OneToOneField(
        user_models.User,
        related_name='freshchat_user',
        on_delete=models.CASCADE,
        verbose_name=_('User')
    )
    freshchat_user_id = models.CharField(
        max_length=512,
        null=True,
        blank=True
    )
