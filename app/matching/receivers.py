from django.db.models.signals import post_save

from django.dispatch import receiver

from matching import public
from matching import models
from users import models as user_models


# @receiver(post_save, sender=user_models.Profile)
def update_or_create_user_score_on_profile_update(sender, instance, *args, **kwargs):
    """Update or create user score if the user model gets updated"""
    user = instance.user
    score = public.calculate_user_score(user)
    try:
        user_score, created = models.UserScore.objects.update_or_create(
            user=user,
            defaults={"score": score}
        )
    except models.UserScore.MultipleObjectsReturned:
        # In cases where we have multiple objects.
        user_score = models.UserScore.objects.filter(user=user).first()
        user_score.score = score
        user_score.save()

    user.score = user_score.score
    user.save()
