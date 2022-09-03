from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from crater.creator import models as creator_models
from crater.payments import models as payment_models, constants as payment_constants
from crater.rewards import models as reward_models
from crater.rewards import serializers as reward_serializers
from crater.sales import constants, models, serializers
from users import permissions as user_permissions
from crater.payments import models as payment_models
from crater.payments import constants as payment_constants
from crater.sales import tasks


# List API for all reward sales, creator specific reward sales and reward sale retrieve
# Creation of Reward sale log, once the user makes the purchase.
# Marking Reward sale log processed by the creator.


class RewardSaleViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.RewardSaleSerializer
    queryset = models.RewardSale.objects.filter(
        is_closed=False,
    ).select_related(
        "reward"
    )
    filterset_fields = ["reward", "reward__creator", "payment_type"]

    def create(self, request, *args, **kwargs):

        data = request.data
        user = request.user
        reward_data = {
            "title": data["title"],
            "photo": data["photo"],
            "description": data["description"],
            "creator": user.creator.id,
            "name": data["title"],
        }
        reward_serialzer = reward_serializers.RewardSerializer(data=reward_data)
        reward_serialzer.is_valid(raise_exception=True)
        print(reward_serialzer.data)
        return Response({}, status=status.HTTP_200_OK)


class RewardSaleLogViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticated]
    serializer_class = serializers.RewardSaleLogSerializer
    queryset = models.RewardSaleLog.objects.all()
    filterset_fields = ["reward_sale", "user"]

    def create(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        payment_type = data.get("payment_type")
        data["user"] = user.pk

        if payment_type == constants.SALE_PAYMENT_TYPE_UPI_ENUM:
            # Create payment object and append payment object to sale log
            amount = data["price"] * data["quantity"]
            payment = payment_models.Payment.objects.create(
                user=user,
                amount=amount,
                gateway=payment_constants.PAYMENT_GATEWAY_CREATOR_UPI_ENUM
            )
            data["payment"] = payment.id
            
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        instance = serializer.save()

        tasks.send_notification_to_creator_for_sale.delay(instance.id)
        response_serializer = self.get_serializer(instance)
        headers = self.get_success_headers(serializer.data)
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(
        methods=["POST"],
        detail=True,
    )
    def accept(self, request, pk, *args, **kwargs):
        # User accepts the payment
        try:
            sale_log = models.RewardSaleLog.objects.get(id=pk)
        except models.RewardSaleLog.DoesNotExist:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        # set sale log to confirmed and payment object also to confirmed
        sale_log.status = constants.SALE_PAYMENT_CONFIRMED_ENUM
        sale_log.save()

        sale_log.reward_sale.update_quantity(sale_log.quantity)

        # Send notification to user
        tasks.send_notification_user_sale_accepted.delay(sale_log.id)
        return Response({}, status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=True,
    )
    def decline(self, request, pk, *args, **kwargs):
        # User decline the payment
        try:
            sale_log = models.RewardSaleLog.objects.get(id=pk)
        except models.RewardSaleLog.DoesNotExist:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        # set sale log to declined and payment object also to confirmed
        sale_log.status = constants.SALE_PAYMENT_DECLINED_ENUM
        sale_log.save()

        # Send notification to user
        tasks.send_notification_user_sale_declined.delay(sale_log.id)
        return Response({}, status=status.HTTP_200_OK)


class RewardSaleItemsViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.RewardDetailWithRewardSaleSerializer
    queryset = reward_models.Reward.objects.prefetch_related(
        "sale"
    ).select_related(
        "creator"
    ).filter(
        is_active=True,
        sale__is_active=True,
        sale__is_closed=False
    ).order_by(
        "-order",
        "created_at"
    ).distinct()
    filterset_fields = ["sale__payment_type", "type__name"]

    @action(
        methods=["GET"],
        detail=False
    )
    def featured(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().exclude(
                photo=""
            )
        )[:3]
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)


class RewardSaleSellersViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.RewardSellerDetailSerializer
    queryset = reward_models.Reward.objects.prefetch_related(
        "sale"
    ).select_related(
        "creator",
        "creator__user",
        "creator__user__profile"
    ).filter(
        is_active=True,
        sale__is_active=True,
        sale__is_closed=False,
    )

    @action(
        methods=["GET"],
        detail=False
    )
    def featured(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        creator_ids = queryset.values_list("creator", flat=True).distinct()
        sellers = creator_models.Creator.objects.filter(id__in=creator_ids)
        serializer = self.get_serializer(sellers, many=True)
        return Response(serializer.data)
