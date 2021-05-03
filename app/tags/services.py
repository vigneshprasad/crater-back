from tags.models import SourceWebsite
from django.db.models.functions import Lower


def get_websites():
    """Get active source websites for articles."""
    return SourceWebsite.objects.filter(is_active=True).order_by(Lower('name'))
