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
    serializer_class = serializers.AuctionSerializer
    queryset = models.Auction.objects.filter(is_closed=False)
    filterset_fields = ["coin__creator"]

    def _get_active_auction(self, creator):
        now = timezone.now()
        auctions = self.get_queryset().filter(
            start__lte=now,
            end__gte=now,
            coin__creator_id=creator
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
            pk(str): Creator ID we are getting the active
                auctions for.

        """
        auctions = self._get_active_auction(pk)

        if not auctions:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serialized = self.get_serializer(auctions[0])
        return Response(serialized.data)
    
    @action(
        methods=["GET"],
        detail=True
    )
    def summary(self, request, pk, *args, **kwargs):
        """Returns auction summary for a creator coin

        Args:
            pk (string): Creator Coin ID

        """
        try:
            auctions = self.get_queryset().filter(coin=pk)
            total_coins = 0
            for auction in auctions:
                total_coins += auction.number_of_coins
            holding = exchange_models.UserCoinHolding.objects.get(
                user=request.user,
                coin=pk
            )
            return Response({
                "total_coins": total_coins,
                "tokens_circulation": holding.number_of_coins
            }, status=status.HTTP_200_OK)

        except (models.Auction.DoesNotExist, exchange_models.UserCoinHolding.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)


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
            if bid.auction.coin.creator.user != request.user:
                # TODO(Abhishek): Create valid Exception
                raise Exception
            bid.status = models.Bid.BID_STATUS_CHOICES[2][0]
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
        bids = self.get_queryset().filter(auction__coin=pk)
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
