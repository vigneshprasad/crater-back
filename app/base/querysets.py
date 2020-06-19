from django.db.models import QuerySet
from django.utils import timezone

class BaseManagerQuerySet(QuerySet):

  def delete(self):
    return super(BaseManagerQuerySet, self).update(deleted_at=timezone.now(), is_deleted=True)

  def hard_delete(self):
    return super(BaseManagerQuerySet, self).delete()

  def restore(self):
    return super(BaseManagerQuerySet, self).update(deleted_at=None, is_deleted=False)