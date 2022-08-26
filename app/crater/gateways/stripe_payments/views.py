from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins
from rest_framework import status

from users import permissions
from rest_framework.response import Response

from crater.gateways.stripe_payments import constants
from crater.gateways.stripe_payments import models
from crater.gateways.stripe_payments import serializers
from crater.gateways.stripe_payments import public

from crater.gateways.stripe_payments.service import stripe_service


class PaymentIntentViewSet(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet
):
    queryset = models.PaymentIntent.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.PaymentIntentSerializer
    lookup_field = "client_secret"

    def create(self, request, *args, **kwargs):
        """Create a Payment intent on our and Stripe's side."""
        user = request.user
        data = request.data
        customer = stripe_service.get_or_create_customer(user)
        intent = stripe_service.create_payment_intent(
            amount=data.get("amount"),
            customer=customer,
            payment_id=data.get("payment"),
            product_id=data.get("product_id"),
            capture_method=constants.DEFAULT_CAPTURE_METHOD,
        )
        serialized = self.get_serializer(intent)
        return Response(serialized.data, status=status.HTTP_201_CREATED)


class StripeWebhookViewSet(
    mixins.CreateModelMixin,
    GenericViewSet
):

    def create(self, request, *args, **kwargs):
        """Webhook from Stripe which listen to change in
            PaymentIntent and Charge state changes.

        """
        data = request.data
        event_type = request.data.get("type")
        if not event_type:
            return Response(status=status.HTTP_200_OK)

        # Payment Intent Events
        if event_type.find("payment_intent") > -1:
            intent_id = data["data"]["object"]["id"]

            try:
                payment_intent = models.PaymentIntent.objects.get(intent_id=intent_id)
            except models.PaymentIntent.DoesNotExist:
                return Response(status=status.HTTP_200_OK)

            intent_object = data["data"]["object"]
            payment_intent.data = intent_object
            payment_intent.save()

            # Update charges related to the Payment Intent.
            charges = intent_object["charges"]["data"]
            public.create_or_update_charges_list(charges)

        # Payment Charge Events
        if event_type.find("charge") > -1:
            charge_data = data["data"]["object"]
            public.create_or_update_charge_object(charge_data)

            if event_type == constants.WEBHOOK_EVENT_TYPE_CHARGE_SUCCEEDED:
                intent_id = charge_data["payment_intent"]
                stripe_service.retrieve_and_update_payment_intent(intent_id)
                public.handle_charge_succeeded(charge_data)

            if event_type == constants.WEBHOOK_EVENT_TYPE_CHARGE_CAPTURED:
                public.handle_charge_captured(charge_data)

        return Response(status=status.HTTP_200_OK)
