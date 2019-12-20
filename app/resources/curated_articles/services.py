from resources.curated_articles.models import CuratedArticle, SourceWebsite
from resources.curated_articles.serializers import CuratedArticleSerializer


def get_curated_articles():
    return CuratedArticle.objects.all()


def get_websites():
    return SourceWebsite.objects.all()


def get_company_curated_articles_data():
    return CuratedArticleSerializer(CuratedArticle.objects.all()[:8], many=True).data
