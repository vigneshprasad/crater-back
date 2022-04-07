from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from leaderboard import models
from leaderboard import tasks


@receiver(post_save, sender=models.Challenge)
def create_leaderboards_for_challenge(sender, instance, *args, **kwargs):
    """Create leaderboards for challenge.

    Args:
        sender(Challenge.__class__): Class representation of Challenge.
        instance(Challenge): Challenge object which was created.
    """
    if not kwargs.get("created"):
        return

    tasks.create_leaderboards_for_challenge.delay(instance.id)


@receiver(m2m_changed, sender=models.Challenge.participants.through)
def create_user_leaderboard_for_challenge(sender, instance, *args, **kwargs):

    action = kwargs.get("action")
    challenge = instance
    leaderboards = challenge.leaderboards.all()

    if action not in ["post_add", "post_remove"]:
        return None

    pk_set = list(kwargs.get("pk_set", []))
    if not pk_set:
        return None

    # On addition of participant, create user leaderboard
    # for the user and leaderboard.
    if action == "post_add":
        for user in pk_set:
            for leaderboard in leaderboards:
                models.UserLeaderboard.objects.update_or_create(
                    user_id=user,
                    leaderboard=leaderboard,
                    defaults={
                        "is_active": True
                    }
                )

    # On removal, mark the user's leaderboard as inactive.
    if action == "post_remove":
        for leaderboard in leaderboards:
            models.UserLeaderboard.objects.filter(
                user_id__in=pk_set,
                leaderboard=leaderboard,
            ).update(is_active=False)


@receiver(m2m_changed, sender=models.Leaderboard.participants.through)
def create_user_leaderboard_for_leaderboard(sender, instance, *args, **kwargs):

    action = kwargs.get("action")
    leaderboard = instance

    if action not in ["post_add", "post_remove"]:
        return None

    pk_set = list(kwargs.get("pk_set", []))
    if not pk_set:
        return None

    # On addition of participant, create user leaderboard
    # for the user and leaderboard.
    if action == "post_add":
        for user in pk_set:
            models.UserLeaderboard.objects.update_or_create(
                user_id=user,
                leaderboard=leaderboard,
                defaults={
                    "is_active": True
                }
            )

    # On removal, mark the user's leaderboard as inactive.
    if action == "post_remove":
        models.UserLeaderboard.objects.filter(
            user_id__in=pk_set
        ).update(is_active=False)
