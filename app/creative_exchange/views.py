from rest_framework import viewsets, mixins, permissions

from . import models, serializers


class ExchangeCategoryViewSet(mixins.RetrieveModelMixin,
                              mixins.ListModelMixin,
                              viewsets.GenericViewSet):
    queryset = models.ExchangeCategory.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ExchangeCategorySerializer
