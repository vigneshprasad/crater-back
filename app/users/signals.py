from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

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
