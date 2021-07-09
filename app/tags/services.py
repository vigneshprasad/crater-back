from django.db.models.functions import Lower

from tags import models


def get_websites():
    """Get active source websites for articles."""
    return models.SourceWebsite.objects.filter(is_active=True).order_by(Lower('name'))


def get_all_tags():
    """Get all active tags."""
    return models.Tag.objects.filter(is_active=True)
