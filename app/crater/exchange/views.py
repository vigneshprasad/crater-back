from rest_framework import mixins
from rest_framework import viewsets

from crater.exchange import models
from crater.exchange import serializers
from users import permissions as user_permissions


class TransactionViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):

    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.TransactionSerializer
    queryset = models.Transaction.objects.all()


class UserCoinHoldingViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):

    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.UserCoinHoldingSerializer
    queryset = models.UserCoinHolding.objects.all()
    filterset_fields = ["user", "coin"]


class UserRewardViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.UserRewardSerializer
    queryset = models.UserReward.objects.all()
    filterset_fields = ["user", "reward"]