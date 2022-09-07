<<<<<<< HEAD
from rest_framework import mixins, status, viewsets
=======
import datetime

from rest_framework import mixins, viewsets, status
>>>>>>> e3f0071007358e5003d463f5de8d46e8330a3ed7
from rest_framework.decorators import action
from rest_framework.response import Response

from crater.creator import models as creator_models
from crater.payments import constants as payment_constants, models as payment_models
from crater.rewards import models as reward_models, serializers as reward_serializers
from crater.sales import constants, models, serializers, signals
from users import permissions as user_permissions
from crater.payments import models as payment_models
from crater.payments import constants as payment_constants
from crater.sales import tasks
from tokens import models as token_models
from tokens import constants as token_constants
from tokens import public as tokens_public

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
        """Creates a reward sale for creator."""
        data = request.data
        user = request.user

        reward_data = {
            "title": data["title"],
            "photo": data.get("photo", None),
            "description": data["description"],
            "creator": user.creator.id,
            "name": data["title"],
            "type": data["type"]
        }
        reward_serializer = reward_serializers.RewardSerializer(data=reward_data)
        reward_serializer.is_valid(raise_exception=True)
        reward_instance = reward_serializer.save()

        reward_sale_data = {
            "price": data["price"],
            "quantity": data["quantity"],
            "payment_type": constants.SALE_PAYMENT_TYPE_UPI_ENUM,
            "reward": reward_instance.id
        }

        reward_sale_serializer = self.get_serializer(data=reward_sale_data)
        reward_sale_serializer.is_valid(raise_exception=True)
        reward_sale_instance = reward_sale_serializer.save()

        response_serializer = self.get_serializer(reward_sale_instance)

        return Response(response_serializer.data, status=status.HTTP_200_OK)


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
        """API for when a user purchases a reward sale."""
        data = request.data
        user = request.user
        payment_type = data.get("payment_type")
        data["user"] = user.pk

        reward_sale_id = data["reward_sale"]
        # Check if the reward sale associated with the ID is active.
        reward_sale = models.RewardSale.objects.filter(id=reward_sale_id, is_active=True).first()
        # If the reward sale is not active, return and error from here.
        if not reward_sale:
            return Response({
                "message": "Reward sale can't be purchased."
            }, status=status.HTTP_400_BAD_REQUEST)

        if payment_type == constants.SALE_PAYMENT_TYPE_UPI_ENUM:
            # Create payment object and append payment object to sale log
            # only if the user is paying FIAT currency.
            amount = data["price"] * data["quantity"]
            payment = payment_models.Payment.objects.create(
                user=user,
                amount=amount,
                gateway=payment_constants.PAYMENT_GATEWAY_CREATOR_UPI_ENUM
            )
            data["payment"] = payment.id

        if payment_type == constants.SALE_PAYMENT_TYPE_LEARN_ENUM:
            amount = data["price"] * data["quantity"]
            valid = tokens_public.validate_token_redeem_for_user(user, amount)
            if not valid:
                return Response({
                    "type": "TokensInsufficient",
                    "message": "You do not have enough LEARN tokens for purchase"
                }, status=status.HTTP_400_BAD_REQUEST)

            token_models.UserTokenLog.objects.create(
                user=user,
                amount=amount,
                type=token_constants.TRANSACTION_TYPE_REDEEMED_ENUM,
                date=datetime.date.today()
            )

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        if payment_type == constants.SALE_PAYMENT_TYPE_UPI_ENUM:
            # Send sale created signal.
            signals.sale_created.send(sender=instance.__class__, sale_log=instance)

        response_serializer = self.get_serializer(instance)
        headers = self.get_success_headers(serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(
        methods=["POST"],
        detail=True,
    )
    def accept(self, request, pk, *args, **kwargs):
        """API for when a creator accept/confirms a sale, i.e. payment
            has been made for a sale.

        """
        try:
            sale_log = models.RewardSaleLog.objects.get(id=pk)
        except models.RewardSaleLog.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Mark the sale confirmed.
        sale_log.mark_sale_confirmed()
        return Response({}, status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=True,
    )
    def decline(self, request, pk, *args, **kwargs):
        """API for when a creator declines a sale, i.e. payment
            has not been made for a sale.

        """
        try:
            sale_log = models.RewardSaleLog.objects.get(id=pk)
        except models.RewardSaleLog.DoesNotExist:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        # Mark the sale declined.
        sale_log.mark_sale_declined()
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
        "creator",
        "creator__user",
        "creator__user__profile"
    ).filter(
        is_active=True,
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
