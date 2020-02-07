from django.db.models.signals import pre_save
from django.dispatch import receiver

from community.posts.models import File
from users.models import CoverFile


@receiver(pre_save, sender=File)
def post_transcode_file(sender, instance, *args, **kwargs):
    if not instance.file or instance.file.file != instance.object:
        instance.file = CoverFile.objects.create(file=instance.object, user=instance.post.creator)
