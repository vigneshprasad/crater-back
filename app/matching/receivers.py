from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from django.dispatch import receiver

from matching import public
from matching import models


@receiver(post_save, sender=get_user_model())
def update_or_create_user_score(sender, instance, created, *args, **kwargs):
    """If the user models score changes, change the score on UserScore as well."""
    user_score = models.UserScore.objects.filter(user=instance).last()

    # If there is no user score created. Create a user score here.
    if not user_score:
        score = public.get_user_matching_score(instance)
        return models.UserScore.objects.create(
            user=instance,
            score=score
        )

    if user_score.score == instance.score:
        return

    # If user score is separate from UserScore table score
    # update the UserScore table.
    user_score.score = instance.score
    user_score.save()
