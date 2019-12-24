from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import MarketingCategoryProxy


@receiver(pre_save, sender=MarketingCategoryProxy)
def marketing_pre_save(sender, instance, *args, **kwargs):
    instance.direction = 'marketing'
