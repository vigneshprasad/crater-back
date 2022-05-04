from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from crater.auctions import constants, models, serializers, signals, filters
from users import permissions as user_permissions


class AuctionViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.RewardAuctionBaseSerializer
    queryset = models.RewardAuction.objects.filter(
        is_active=True,
        is_closed=False,
        end__gt=timezone.now()
    )
    filterset_fields = ["reward"]

    def _get_active_auction(self, reward):
        """Get active auctions for reward ID."""
        now = timezone.now()
        return self.get_queryset().filter(
            start__lte=now,
            end__gte=now,
            reward_id=reward
        ).order_by("-start")

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

    def create(self, request, *args, **kwargs):
        auction_id = kwargs.get("auction")
        
        return super(BidViewSet, self).create(request, *args, **kwargs)

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
        bids = self.get_queryset().filter(
            creator=pk,
            status__in=[
                constants.BID_STATUS_ACCEPTED_ENUM,
                constants.BID_STATUS_PENDING_ENUM,
                constants.BID_STATUS_CANCELLED_ENUM,
                constants.BID_STATUS_REJECTED_ENUM
            ]
        )
        bids_accepted = bids.filter(status=constants.BID_STATUS_ACCEPTED_ENUM)
        total_received = 0
        total_bids = bids.count()
        total_accepted = bids_accepted.count()
        net_worth = 0

        for bid in bids:
            total_received += bid.amount

        for bid in bids_accepted:
            net_worth += bid.amount
        
        return Response({
            "total_net_worth": total_received,
            "accepted_net_worth": net_worth,
            "total_bids": total_bids,
            "total_accepted": total_accepted
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
