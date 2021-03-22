from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from django.dispatch import receiver

from matching import public
from matching import models
from users import models as user_models


# TODO(Nishant): Make these live once we are ready with the scoring.
# @receiver(post_save, sender=get_user_model())
def update_or_create_user_score(sender, instance, *args, **kwargs):
    """Update or create user score if the user model gets updated"""
    user = instance

    score = public.get_user_matching_score(user)
    user_score, created = models.UserScore.objects.update_or_create(
        user=user,
        defaults={"score": score}
    )
    user_score.score = instance.score
    user_score.save()


# @receiver(post_save, sender=user_models.Profile)
def update_or_create_user_score(sender, instance, *args, **kwargs):
    """Update or create user score if the user model gets updated"""
    user = instance.user

    score = public.get_user_matching_score(user)
    user_score, created = models.UserScore.objects.update_or_create(
        user=user,
        defaults={"score": score}
    )
    user_score.score = instance.score
    user_score.save()
