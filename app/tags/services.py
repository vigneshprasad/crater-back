from tags.models import SourceWebsite


def get_websites():
    return SourceWebsite.objects.all()
