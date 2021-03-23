from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from django.dispatch import receiver

from matching import public
from matching import models
from users import models as user_models


@receiver(post_save, sender=user_models.Profile)
def update_or_create_user_score_on_profile_update(sender, instance, *args, **kwargs):
    """Update or create user score if the user model gets updated"""
    user = instance.user

    score = public.get_user_matching_score(user)
    user_score, created = models.UserScore.objects.update_or_create(
        user=user,
        defaults={"score": score}
    )
    user.score = user_score.score
    user.save()
