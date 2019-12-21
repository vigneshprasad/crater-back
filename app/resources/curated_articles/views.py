from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from resources.curated_articles.paginators import CuratedArticlePagination
from resources.curated_articles.serializers import CuratedArticleSerializer
from resources.curated_articles.services import get_curated_articles


class CuratedArticleViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    serializer_class = CuratedArticleSerializer
    pagination_class = CuratedArticlePagination
    queryset = get_curated_articles()
    permission_classes = (IsAuthenticated,)
    filterset_fields = ['tag', 'website_tag']
