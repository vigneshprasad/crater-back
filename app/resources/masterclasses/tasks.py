from django.db.models import F
from resources.masterclasses.models import MasterClass

from freelance.celery import app


@app.task
def masterclass_count_views(pk):
    MasterClass.objects.filter(pk=pk).update(count=F('count')+1)
