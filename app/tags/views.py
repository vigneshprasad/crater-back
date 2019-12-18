from rest_framework import viewsets, mixins, permissions

from . import models, serializers
from .serializers import ArticleTagSerializer


class TagViewSet(mixins.RetrieveModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    queryset = models.Tag.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.TagSerializer


class MasterClassViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = models.MasterClassTag.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.MasterClassTagSerializer


class ArticleTagViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ArticleTagSerializer
    queryset = models.ArticleTag.objects.all()
    permission_classes = [permissions.IsAuthenticated]
