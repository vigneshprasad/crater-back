import datetime

from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from sklearn.metrics import auc


from crater.auctions import constants, models
from crater.creator import private
from crater.auctions import serializers
from crater.auctions import signals
from crater.auctions import filters
from crater.exchange import models as exchange_models
from users import permissions as user_permissions


class AuctionViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.RewardAuctionBaseSerializer
    queryset = models.RewardAuction.objects.filter(is_closed=False)
    filterset_fields = ["reward"]

    def _get_active_auction(self, reward):
        now = timezone.now()
        auctions = self.get_queryset().filter(
            start__lte=now,
            end__gte=now,
            reward_id=reward
        ).order_by("-start")
        return auctions

    @action(
        methods=["GET"],
        detail=True
    )
    def active_auction(self, request, pk):
        """Returns active auctions for a creator.

        Args:
            request(Request): Request object.
            pk(str): Reward ID we are getting the active
                auctions for.

        """
        auctions = self._get_active_auction(pk)

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
    queryset = models.Bid.objects.all().order_by("-created_at")
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.BidsFilters

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[user_permissions.IsAuthenticated]
    )
    def accept(self, request, *args, pk, **kwargs):

        try:
            bid = self.get_queryset().get(pk=pk)
            if bid.creator.user != request.user:
                # TODO(Abhishek): Create valid Exception
                raise Exception
            bid.status = constants.BID_STATUS_ACCEPTED_ENUM
            bid.save()
            signals.bid_accepted.send(sender=bid.__class__, bid=bid)
            # Update accepted status

            # Create Coin Price Log
            # Charge signal
            # -> Update is_processed after charge, Create Transaction Log
            # -> Assign coins in CoinHolding to User
            serialized = self.get_serializer(bid)
            return Response(serialized.data, status=status.HTTP_200_OK)
        except models.Bid.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    
    @action(
        methods=["GET"],
        detail=True,
        permission_classes=[user_permissions.IsAuthenticated]
    )
    def summary(self, request, pk, *args, **kwargs):
        """Returns summary of bids for a creator id.

        Args:
            request:
            pk: CreatorId: for getting summery of creatos bid
            *args:
            **kwargs:

        """
        bids = self.get_queryset().filter(creator=pk)
        bids_accepted = bids.filter(status=constants.BID_STATUS_ACCEPTED_ENUM)
        total_recieved = 0
        net_worth = 0

        for bid in bids:
            total_recieved += bid.amount

        for bid in bids_accepted:
            net_worth += bid.amount
        
        return Response({
            "total_recieved": total_recieved,
            "net_worth": net_worth
        }, status=status.HTTP_200_OK)


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
