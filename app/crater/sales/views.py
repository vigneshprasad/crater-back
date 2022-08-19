from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from crater.sales import constants, models, serializers
from users import permissions as user_permissions


# List API for all reward sales, creator specific reward sales and reward sale retrieve
# Creation of Reward sale log, once the user makes the purchase.
# Marking Reward sale log processed by the creator.


class RewardSaleViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticated]
    serializer_class = serializers.RewardSaleSerializer
    queryset = models.RewardSale.objects.filter(
        is_active=True,
    )
    filterset_fields = ["reward"]


class RewardSaleLogViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticated]
    serializer_class = serializers.RewardSaleLogSerializer
    queryset = models.RewardSaleLog.objects.all()
    filterset_fields = ["reward_sale", "user"]
