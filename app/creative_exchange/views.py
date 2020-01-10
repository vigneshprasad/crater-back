from rest_framework import viewsets, mixins, permissions

from community.mixins import SetCreatorRequestDataMixin
from users.paginators import Pagination
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
    queryset = models.ExchangeRequest.objects.all().order_by('-id')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ExchangeRequestSerializer
    pagination_class = Pagination
