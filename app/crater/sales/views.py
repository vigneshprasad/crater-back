from crypt import methods
from urllib import response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from crater.sales import constants, models, serializers
from users import permissions as user_permissions
from crater.payments import models as payment_models
from crater.payments import constants as payment_constants


# List API for all reward sales, creator specific reward sales and reward sale retrieve
# Creation of Reward sale log, once the user makes the purchase.
# Marking Reward sale log processed by the creator.


class RewardSaleViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticated]
    serializer_class = serializers.RewardSaleSerializer
    queryset = models.RewardSale.objects.filter(
        is_active=True,
    )
    filterset_fields = ["reward", "reward__creator"]


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
        response_serializer = self.get_serializer(instance)
        headers = self.get_success_headers(serializer.data)
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(
        methods=["POST"],
        detail=True,
    )
    def accept(self, request, pk, *args, **kwargs):
        # User accepts the payment
        # set sale log to confirmed and payment object also to confirmed
        # Send notification to user
        return Response({}, status=status.HTTP_200_OK)
    

    @action(
        methods=["POST"],
        detail=True,
    )
    def decline(self, request, pk, *args, **kwargs):
        # User decline the payment
        # set sale log to declined and payment object also to declined
        # Send notification to user
        return Response({}, status=status.HTTP_200_OK)