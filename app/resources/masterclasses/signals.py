from django.db.models import Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from notifications.models import Notification, UserNotification
from resources.masterclasses.models import MasterClass
from users.models import User, CoverFile


@receiver(post_save, sender=MasterClass)
def master_class_notification(sender, instance,  created, *args, **kwargs):
    if created:
        notification = Notification.objects.create(master_class=instance)
        users = User.objects.filter(profile__isnull=False)
        for user in users:
            UserNotification.objects.create(user=user, notification=notification)


@receiver(pre_save, sender=MasterClass)
def master_class_transcode_cover(sender, instance, *args, **kwargs):
    if not instance.file or instance.file.file != instance.cover:
        admin = User.objects.filter(Q(email='admin@admin.com') | Q(groups__name__in=['Admin', 'Support'])).first()
        instance.file = CoverFile.objects.create(file=instance.cover, user=admin)
