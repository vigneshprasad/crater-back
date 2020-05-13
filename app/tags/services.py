from tags.models import SourceWebsite
from django.db.models.functions import Lower


def get_websites():
    return SourceWebsite.objects.all().order_by(Lower('name'))
