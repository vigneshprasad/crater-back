from django.db.models.signals import pre_save
from django.dispatch import receiver

from tags.models import WorkCityProxy


@receiver(pre_save, sender=WorkCityProxy)
def work_city_pre_save(sender, instance, *args, **kwargs):
    instance.is_work = True
