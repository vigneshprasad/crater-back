from django.db.models.signals import post_save

from django.dispatch import receiver
from django.contrib.auth import get_user_model

from matching import models


@receiver(post_save, sender=get_user_model())
def update_user_score(sender, instance, created, *args, **kwargs):
    """If the user models score changes, change the score on UserScore as well."""
    user_score = models.UserScore.objects.filter(user=instance).last()
    if user_score.score == instance.score:
        return

    user_score.score = instance.score
    user_score.save()
