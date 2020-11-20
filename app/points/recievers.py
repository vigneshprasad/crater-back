from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.exceptions import NotFound

from .models import UserPoints, PointsRule, PointsLog
from users.signals import profile_completed, referal_success_points_signal
from community.posts.signals import (
    post_created,
    post_deleted,
    points_like_received_on_post,
    points_liked_post
)
from community.comments.signals import comment_created_points, comment_created_post_author_points
from community.groups.signals import follower_recieved_signal
from consumers.chat.receivers import new_chat_points_signal
from order.signals import service_complete_buyer_points_signal, service_complete_seller_points_signal
from rewards.signals import package_request_created

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_points(sender, instance, created, *args, **kwargs):
    if created:
        UserPoints.objects.create(
            user=instance,
            points=0
        )


@receiver(profile_completed)
@receiver(post_created)
@receiver(post_deleted)
@receiver(points_like_received_on_post)
@receiver(points_liked_post)
@receiver(comment_created_points)
@receiver(comment_created_post_author_points)
@receiver(follower_recieved_signal)
@receiver(new_chat_points_signal)
@receiver(service_complete_buyer_points_signal)
@receiver(service_complete_seller_points_signal)
@receiver(referal_success_points_signal)
def apply_user_points(sender, rule_key, user, base_factor=1, bonus=0, bonus_factor=1, **kwargs):
    user_points, user_points_created = UserPoints.objects.get_or_create(
        user=user
    )
    try:
        points_rule = PointsRule.objects.get(key=rule_key)
    except PointsRule.DoesNotExist:
        raise NotFound
    user_points.points = user_points.points + points_rule.points_value * base_factor + bonus * bonus_factor
    user_points.save()
    PointsLog.objects.create(
        user=user,
        action=points_rule,
        base_points_value=points_rule.points_value,
        base_factor=base_factor,
        bonus_points_value=bonus,
        bonus_factor=bonus_factor
    )


@receiver(package_request_created)
def apply_package_creation_points(sender, user, points_applied, **kwargs):
    package_rules_key = 14
    user_points, user_points_created = UserPoints.objects.get_or_create(
        user=user
    )
    try:
        points_rule = PointsRule.objects.get(key=package_rules_key)
    except PointsRule.DoesNotExist:
        raise NotFound

    user_points.points = user_points.points + (points_rule.points_value * (-points_applied))
    user_points.save()
    PointsLog.objects.create(
        user=user,
        action=points_rule,
        base_points_value=points_rule.points_value,
        base_factor=(-points_applied),
        bonus_points_value=0,
        bonus_factor=1,
    )
