from rest_framework import viewsets, mixins
from django.db.models.functions import Lower

from . import models, serializers
from users import permissions


class IndustryViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = models.Industry.objects.all().order_by(Lower('name'))
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.IndustrySerializer


class FundingViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    queryset = models.Funding.objects.all().order_by(Lower('name'))
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.FundingSerializer


class CompanyViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    queryset = models.Company.objects.all().order_by(Lower('name'))
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.CompanySerializer
