import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response


from crater.auctions import models
from crater.creator import private
from crater.auctions import serializers
from crater.creator import signals
from users import permissions as user_permissions


class AuctionViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.AuctionSerializer
    queryset = models.Auction.objects.filter(is_closed=False)
    filterset_fields = ["coin__creator"]

    @action(
        methods=["GET"],
        detail=True
    )
    def active_auction(self, request, pk):
        """Returns active auctions for a creator.

        Args:
            request(Request): Request object.
            pk(str): Creator ID we are getting the active
                auctions for.

        """
        now = timezone.now()
        auctions = self.get_queryset().filter(
            start__lte=now,
            end__gte=now,
            coin__creator_id=pk
        ).order_by("-start")

        if not auctions:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serialized = self.get_serializer(auctions[0])
        return Response(serialized.data)


class BidViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.BidSerializer
    queryset = models.Bid.objects.all().order_by("bid_time")
    filterset_fields = ["bidder", "auction", "status"]


class CoinPriceLogViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.CoinPriceLogSerializer
    queryset = models.CoinPriceLog.objects.all()
    filterset_fields = ["coin", "coin__creator"]
