from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver, Signal

from users.models import Referral


@receiver(pre_save, sender=get_user_model())
def create_push_and_rent(sender, instance, *args, **kwargs):
    if not instance.name:
        instance.name = f'{instance.first_name} {instance.last_name}'
    return instance


@receiver(post_save, sender=get_user_model())
def set_referrer_relation(sender, instance, *args, **kwargs):
    if instance.referer:
        Referral.objects.get_or_create(user=instance)

user_updated = Signal(providing_args=[
    "user",
])

user_signed_up = Signal(providing_args=[
    "user",
])

objectives_added = Signal(providing_args=[
    "user",
    "objectives",
])

email_verified = Signal(providing_args=[
    "user",
])

basic_profile_created = Signal(providing_args=[
    "user",
    "request",   
    "response" 
])

phone_number_verified = Signal(providing_args=[
    "user",
    "request"
])

service_created = Signal(providing_args=[
    "user",
    "request",
    "response"
])

referred_friend = Signal(providing_args=[
    "user",
    "request",    
])

profile_completed = Signal(providing_args=[
    "rule_key",
    "user",
])

referal_success_points_signal = Signal(providing_args=[
    "rule_key",
    "user",
])