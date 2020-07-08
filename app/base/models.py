from django.db import models
from django.utils import timezone

from .managers import BaseModelManager


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    objects = BaseModelManager()
    all_objects = BaseModelManager(with_deleted=True)

    class Meta:
        abstract = True

    def delete(self, soft=True):
        if soft:
            self.deleted_at = timezone.now()
            self.is_deleted = True
            self.save()
        else:
            super(BaseModel, self).delete()

    def restore(self):
        self.deleted_at = None
        self.is_deleted = False
        self.save()
