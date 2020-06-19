from django.db import models
from .querysets import BaseManagerQuerySet

class BaseModelManager(models.Manager):

  def __init__(self, *args, **kwargs):
    self.with_deleted = kwargs.pop('with_deleted', False)
    super(BaseModelManager, self).__init__(*args, **kwargs)

  def get_queryset(self):
    if self.with_deleted:
      return BaseManagerQuerySet(self.model, using=self._db)
    return BaseManagerQuerySet(self.model, using=self._db).filter(is_deleted=False)

  def hard_delete(self):
    return self.get_queryset().hard_delete()

  def delete(self):
    return self.get_queryset().delete()

  def restore(self):
    return self.get_queryset().restore()