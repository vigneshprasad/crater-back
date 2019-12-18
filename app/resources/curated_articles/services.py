from resources.curated_articles.models import CuratedArticle, SourceWebsite


def get_curated_articles():
    return CuratedArticle.objects.all()


def get_websites():
    return SourceWebsite.objects.all()
