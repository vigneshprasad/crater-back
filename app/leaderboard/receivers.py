from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from leaderboard import models


@receiver(m2m_changed, sender=models.Leaderboard.participants.through)
def create_user_leaderboard(sender, instance, *args, **kwargs):

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
                user=user,
                leaderboard=leaderboard,
                defaults={
                    "is_active": True
                }
            )

    # On removal, mark the user's leaderboard as inactive.
    if action == "post_remove":
        models.UserLeaderboard.objects.filter(
            user__in=pk_set
        ).update(is_active=False)
