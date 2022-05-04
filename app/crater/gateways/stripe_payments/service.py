import logging
import stripe

from django.conf import settings

from crater.gateways.stripe_payments import constants
from crater.gateways.stripe_payments import models


class StripePaymentService:
    """Stripe service."""

    def __init__(self, api_key):
        """Initialize the SDK with our API key."""
        self.stripe = stripe
        self.stripe.api_key = api_key

    def get_or_create_customer(self, user):
        """Gets or creates customer on Stripe's end.

        Args:
            user(User): User whose customer object we are
                getting/creating.

        """
        try:
            stripe_customer = models.Customer.objects.get(
                user=user
            )
        except models.Customer.DoesNotExist:
            # Create customer on Stripe.
            customer = self.stripe.Customer.create(
                name=user.display_name,
                phone=user.phone_number,
                email=user.email
            )
            # Add the customer to our backend.
            stripe_customer = models.Customer.objects.create(
                user=user,
                customer_id=customer["id"]
            )

        return stripe_customer

    def update_customer(self, *kwargs):
        pass

    def retrieve_and_update_payment_intent(self, intent_id: str):
        """Retrieve Payment intent from Stripe's end and update
            on our backend.

        Args:
            intent_id(int): Payment Intent ID on our end.

        """
        try:
            payment_intent_obj = models.PaymentIntent.objects.get(intent_id=intent_id)
        except models.PaymentIntent.DoesNotExist:
            return False

        payment_intent = self.stripe.PaymentIntent.retrieve(intent_id)
        payment_intent_obj.data = payment_intent
        payment_intent_obj.save()

    def create_payment_intent(
            self,
            amount,
            customer,
            payment_id,
            product_id,
            capture_method,
            currency="inr",
            payment_method_types=None,
    ):
        """Creates payment intent on Stripe's end.

        Args:
            amount(float): Amount for the payment being made.
            customer(Customer): Stripe customer object on our end.
            payment_id(int): Payment ID of the payment we are creating
                the intent for.
            product_id(int): Product ID of the product being purchased.
            capture_method(str): What is the capture method of the payment.
            currency(str): What is the currency of the payment amount.
            payment_method_types(list): Payment method types supported.

        """
        # If payment method is not provided, default to card.
        payment_method_types = payment_method_types or constants.DEFAULT_PAYMENT_METHOD_TYPES

        intent = self.stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            customer=customer.customer_id,
            payment_method_types=payment_method_types,
            capture_method=capture_method,
        )
        stripe_intent_object = models.PaymentIntent.objects.create(
            payment_id=payment_id,
            customer_id=customer.id,
            # Storing the amount in Rupees in backend.
            amount=amount / 100,
            client_secret=intent.client_secret,
            product_id=product_id,
            data=intent.to_dict(),
            intent_id=intent.id,
        )
        return stripe_intent_object

    def capture_payment_intent(self, intent, amount=None):
        """Capture payment intent on Stripes end.

        Args:
            intent(PaymentIntent): Payment intent object we are capturing.
            amount(float): Amount we are capturing from the user.

        Note:
            If the amount to be captured is None, Stripe with capture
                the full amount.

        """
        try:
            updated_payment_intent = self.stripe.PaymentIntent.capture(
                intent.intent_id,
                amount_to_capture=amount
            )
        except Exception as e:
            # Log the error if any and return from here.
            logging.error(str(e))
            return False

        intent.data = updated_payment_intent.to_dict()
        intent.save()
        return intent


stripe_service = StripePaymentService(api_key=settings.STRIPE_SECRET_KEY)
