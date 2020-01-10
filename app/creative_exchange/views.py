from rest_framework import viewsets, mixins, permissions

from community.mixins import SetCreatorRequestDataMixin
from . import models, serializers


class ExchangeCategoryViewSet(mixins.RetrieveModelMixin,
                              mixins.ListModelMixin,
                              viewsets.GenericViewSet):
    queryset = models.ExchangeCategory.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ExchangeCategorySerializer


class ExchangeRequestViewSet(SetCreatorRequestDataMixin,
                             mixins.RetrieveModelMixin,
                             mixins.ListModelMixin,
                             mixins.CreateModelMixin,
                             viewsets.GenericViewSet):
    queryset = models.ExchangeRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ExchangeRequestSerializer
