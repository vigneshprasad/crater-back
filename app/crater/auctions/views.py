from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from crater.auctions import constants, models, serializers, filters, exceptions, paginators
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

    def _get_active_auction(self, reward_id):
        """Get active auctions for a reward.

        Args:
            reward_id(int): Reward ID for which we are getting active
                auctions.

        """
        now = timezone.now()
        return self.get_queryset().filter(
            start__lte=now,
            end__gte=now,
            reward_id=reward_id
        ).order_by("-start")

    @action(
        methods=["GET"],
        detail=True
    )
    def active_auction(self, request, pk):
        """Returns active auctions for a creator.

        Args:
            request(Request): Request object.
            pk(int): Reward ID we are getting the active
                auctions for.

        """
        auctions = self._get_active_auction(pk)

        if not auctions:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serialized = self.get_serializer(auctions[0])
        return Response(serialized.data)

    @action(
        methods=["GET"],
        detail=False,
        queryset=models.RewardAuction.objects.filter(
            is_active=True,
            is_closed=False,
            end__gt=timezone.now()
        ).select_related(
            "reward",
            "reward__creator"
        ).order_by(
            "-start"
        ),
        permission_classes=[user_permissions.IsAuthenticatedOrReadOnly],
        serializer_class=serializers.RewardAuctionListSerializer,
        pagination_class=paginators.RewardAuctionPagination,
    )
    def all(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


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
        # TODO(Nishant): Add an exception here if the reward auction
        # has expired.
        return super(BidViewSet, self).create(request, *args, **kwargs)

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[user_permissions.IsAuthenticated]
    )
    def accept(self, request, *args, pk, **kwargs):
        """Accept a bid."""
        try:
            bid = self.get_queryset().get(pk=pk)
        except models.Bid.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if bid.creator.user != request.user:
            user_not_following_creator_exception = exceptions.BidActionNotAllowed()
            return Response(
                user_not_following_creator_exception.get_error_body(),
                status=user_not_following_creator_exception.status_code
            )

        # Mark bid as accepted.
        bid.mark_accepted()

        serialized = self.get_serializer(bid)
        return Response(serialized.data, status=status.HTTP_200_OK)

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
        total_net_worth = 0
        accepted_net_worth = 0
        total_bids = bids.count()
        total_bids_accepted = bids_accepted.count()

        # Calculate total amount bid.
        for bid in bids:
            total_net_worth += bid.amount

        # Calculate total amount accepted.
        for bid in bids_accepted:
            accepted_net_worth += bid.amount

        return Response({
            "total_net_worth": total_net_worth,
            "accepted_net_worth": accepted_net_worth,
            "total_bids": total_bids,
            "total_accepted": total_bids_accepted
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
