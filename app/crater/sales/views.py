import datetime

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from crater.creator import models as creator_models
from crater.payments import constants as payment_constants, models as payment_models
from crater.rewards import models as reward_models, serializers as reward_serializers, constants as reward_constants
from crater.sales import constants, models, serializers, signals
from tokens import constants as token_constants, models as token_models, public as tokens_public
from users import permissions as user_permissions


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

    @action(
        methods=["GET"],
        detail=False
    )
    def featured(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().exclude(
                reward__photo="",
                show_in_store=False
            )
        )[:3]
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @action(
        methods=["GET"],
        detail=False
    )
    def store(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(
                show_in_store=True
            )
        )
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)
        detail=True

    @action(
        methods=["GET"],
        detail=False
    )
    def stream(self, request, pk, *args, **kwargs):
        
        reward = reward_models.Reward.objects.filter(
            type__name=reward_constants.REWARD_NAME_PRIVATE_STREAM,
            object_id=pk,
            is_active=True
        ).first()

        if not reward:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            reward_sale_instance = models.RewardSale.objects.get(reward=reward, is_active=True, is_closed=False)
        except models.RewardSale.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(reward_sale_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


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

        if payment_type == constants.SALE_PAYMENT_TYPE_LEARN_ENUM:
            # In case of learn payment, see if the user has enough tokens
            # for the payment.
            amount = data["price"] * data["quantity"]
            valid = tokens_public.can_redeem_tokens(user, amount)
            if not valid:
                return Response({
                    "type": "TokensInsufficient",
                    "message": "You do not have enough LEARN tokens for purchase"
                }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        # Send signal for sale created.
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
