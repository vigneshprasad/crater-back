from rest_framework import mixins, viewsets

from crater.rewards import models, serializers
from users import permissions as user_permissions


class RewardTypeViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.RewardTypeSerializer
    queryset = models.RewardType.objects.filter(is_active=True)


class RewardViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.RewardSerializer
    queryset = models.Reward.objects.filter(is_active=True).order_by("-order", "created_at")
    filterset_fields = ["creator", "creator__user", "type", "creator__slug"]


class RedemptionViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.RedemptionSerializer
    queryset = models.Redemption.objects.all()
    filterset_fields = ["user", "reward__creator"]
