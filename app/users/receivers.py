import datetime
import logging

from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from users import signals
from users import models


PROFILE_COMPLETED_POINTS_KEY = 1
REFERAL_SUCCESS_POINTS_KEY = 13

User = get_user_model()


@receiver(pre_save, sender=get_user_model())
def check_if_user_name_is_populated(sender, instance, *args, **kwargs):
    """Checks if a user's name is populated for the first time.

    Args:
        sender(User class): Class representation of user model.
        instance(User): Instance being saved.

    """
    # If the model is being created. Return from here.
    if instance._state.adding:
        return

    # Get the model state in the DB before update.
    previous = get_user_model().objects.get(pk=instance.pk)

    # Get previous and current name
    previous_name = None if not previous.name else previous.name.strip()
    current_name = None if not instance.name else instance.name.strip()

    # If there is a previous name, and no current name throw and error.
    if not current_name and previous_name:
        logging.error("Name removed for user: {}".format(previous.__str__()))
        return

    # If there is no previous name and there is a current name. Send name
    # populate signal.
    if not previous_name and current_name:
        signals.user_name_populated.send(
            sender=instance.__class__,
            user=instance
        )


@receiver(signals.user_created)
def create_profile_on_user_creation(sender, user, *args, **kwargs):
    profile, created = models.Profile.objects.get_or_create(user=user)
    return profile


@receiver(pre_save, sender=get_user_model())
def create_push_and_rent(sender, instance, *args, **kwargs):
    if not instance.name:
        instance.name = f"{instance.first_name} {instance.last_name}"
    return instance


@receiver(post_save, sender=User)
def send_profile_completed_points_signal(sender, instance, created, *args, **kwargs):
    signals.user_updated.send(
        sender=instance.__class__,
        user=instance,
    )

    if created:
        signals.user_signed_up.send(
            sender=instance.__class__,
            user=instance
        )


@receiver(signals.profile_requested)
def update_user_activity(sender, profile, **kwargs):
    """Updates user activity on every profile retrieve call.

    Args:
        sender(Profile class): Class value of the profile model.
        profile(Profile): Profile object of the user that made the
            request.

    """
    user_activity, created = models.UserActivity.objects.update_or_create(
        user=profile.user,
        defaults={
            "last_active": datetime.datetime.now()
        }
    )

    return created
