from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from crater.rewards import models
from crater.creator import private
from crater.rewards import serializers
from crater.creator import signals
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
    queryset = models.Reward.objects.filter(is_active=True).order_by("-order")
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
