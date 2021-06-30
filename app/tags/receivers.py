from django.dispatch import receiver
from django.db.models.signals import  post_save

from tags import models
from tags import choices
from users import models as user_models


@receiver(post_save, sender=models.Tag)
def create_profile_extra_info_on_post_save(sender, instance, created, *args, **kwargs):
    if not created:
        return

    user_models.ProfileExtraInfoMeta.objects.create(
        tag=instance,
        question=choices.DEFAULT_EXTRA_INFO_STRING,
    )

