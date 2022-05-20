import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from utils.socket_io_service import socket_io_service
from users import signals
from users import models
from users import tasks
from wn_analytics import constants as analytics_constants


User = get_user_model()
LOGGER = logging.getLogger(__name__)


@receiver(post_save, sender=models.ReferrerBlacklist)
def block_referrals_on_blacklist_addition(sender, instance, *args, **kwargs):
    """Block referrals from chat if the referrer is blacklisted."""
    if not kwargs.get("created"):
        return

    referrer = instance.referrer
    referred_users = referrer.referrals.values_list("user", flat=True)

    # Disable chat for all referrals.
    permissions = models.UserPermission.objects.filter(
        user__in=referred_users,
        allow_chat=True
    )

    for permission in permissions:
        permission.allow_chat = False
        permission.save()


@receiver(post_save, sender=models.UserReferral)
def block_permissions_for_referrer_blacklist(sender, instance, *args, **kwargs):
    """Blocks chat permission for user if the referrer
        is blacklisted.

    """
    if not kwargs.get("created"):
        return

    referred_user = instance.user
    referrer = instance.referrer
    # If the referrer is not blacklisted, return.
    if not hasattr(referrer, "blacklist"):
        return

    if not hasattr(referred_user, "permission"):
        return

    user_permission = referred_user.permission
    user_permission.allow_chat = False
    user_permission.save()


@receiver(post_save, sender=get_user_model())
def send_signal_on_user_creation(sender, instance, *args, **kwargs):
    """Checks if a user's name is populated for the first time.

    Args:
        sender(User class): Class representation of user model.
        instance(User): Instance being saved.

    """
    # If the model is being created. Return from here.
    if not kwargs.get("created"):
        return

    signals.user_created.send(
        sender=instance.__class__,
        user=instance
    )


@receiver(pre_save, sender=models.UserPermission)
def check_if_chat_permission_changed(sender, instance, *args, **kwargs):
    """Send a request to socket.io if a User permission is updated."""
    if instance._state.adding:
        return

    previous = models.UserPermission.objects.get(id=instance.id)
    previous_chat_permission = previous.allow_chat
    current_chat_permission = instance.allow_chat

    if previous_chat_permission == current_chat_permission:
        return

    socket_io_service.send_user_permission(instance)


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
    """Create profile on user creation.

    Args:
        sender(class): User class representation.
        user(User): User object that got created.

    """
    tasks.create_profile_on_user_creation.apply_async(
        args=(user.pk,),
        countdown=60
    )


@receiver(signals.user_created)
def create_user_permission_on_user_creation(sender, user, *args, **kwargs):
    """Create UserPermission on user creation.

    Args:
        sender(class): User class representation.
        user(User): User object that got created.

    """
    try:
        models.UserPermission.objects.get_or_create(user=user)
    except Exception as e:
        LOGGER.error(str(e))
        return


@receiver(signals.user_created)
def create_user_activity_on_user_creation(sender, user, *args, **kwargs):
    """Create user activity entry on user creation

    Args:
        sender(class): User class representation.
        user(User): User object that got created.

    """
    user_activity, _ = models.UserActivity.objects.get_or_create(
        user=user,
        defaults={
            "last_active": timezone.now()
        }
    )


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

    user_activity = models.UserActivity.objects.filter(user=profile.user).last()
    if not user_activity:
        return False

    # Update last active for the user.
    user_activity.last_active = timezone.now()
    user_activity.save()

    return True
