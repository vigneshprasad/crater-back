from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from resources.curated_articles.paginators import CuratedArticlePagination
from resources.curated_articles.serializers import CuratedArticleSerializer, ArticleWebsiteSerializer, \
    ArticleTagSerializer
from resources.curated_articles.services import get_curated_articles, get_tags, get_websites


class CuratedArticleViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    serializer_class = CuratedArticleSerializer
    pagination_class = CuratedArticlePagination
    queryset = get_curated_articles()
    permission_classes = (IsAuthenticated,)
    filterset_fields = ['tag', 'website']


class TagViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = ArticleTagSerializer
    queryset = get_tags()
    permission_classes = (IsAuthenticated,)


class WebsiteViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = ArticleWebsiteSerializer
    queryset = get_websites()
    permission_classes = (IsAuthenticated,)
