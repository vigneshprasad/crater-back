from rest_framework import viewsets, mixins

from . import models, serializers
from .serializers import ArticleTagSerializer, ArticleWebsiteSerializer
from .services import get_websites
from users import permissions


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


class CompanyViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    queryset = models.Company.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.CompanySerializer


class FundingViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    queryset = models.Funding.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.FundingSerializer


class IndustryViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = models.Industry.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.IndustrySerializer


class WebsiteViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ArticleWebsiteSerializer
    queryset = get_websites()
    permission_classes = [permissions.IsAuthenticated]
