from rest_framework import viewsets, mixins
from django.db.models.functions import Lower

from . import models, serializers
from .serializers import ArticleTagSerializer, ArticleWebsiteSerializer
from .services import get_websites
from users import permissions


class TagViewSet(mixins.RetrieveModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    queryset = models.Tag.objects.all().order_by(Lower('name'))
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.TagSerializer


class ObjectiveViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    queryset = models.Objective.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ObjectiveSerializer


class MasterClassViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = models.MasterClassTag.objects.all().order_by(Lower('name'))
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.MasterClassTagSerializer


class ArticleTagViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ArticleTagSerializer
    queryset = models.ArticleTag.objects.all().order_by(Lower('name'))
    permission_classes = [permissions.IsAuthenticated]


class CompanyViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    queryset = models.Company.objects.all().order_by(Lower('name'))
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.CompanySerializer


class FundingViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    queryset = models.Funding.objects.all().order_by(Lower('name'))
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.FundingSerializer


class IndustryViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = models.Industry.objects.all().order_by(Lower('name'))
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.IndustrySerializer


class WebsiteViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ArticleWebsiteSerializer
    queryset = get_websites()
    permission_classes = [permissions.IsAuthenticated]
