import logging
import stripe
from celery.task import task

from django.conf import settings

from crater.gateways.stripe_payments import models
from crater.gateways.stripe_payments import signals


class StripePaymentService:

    def __init__(self, api_key):
        self.stripe = stripe
        self.stripe.api_key = api_key

    def get_or_create_customer(self, user):

        try:
            stripe_customer = models.Customer.objects.get(
                user=user
            )
        except models.Customer.DoesNotExist:
            customer = self.stripe.Customer.create(
                name=user.display_name,
                phone=user.phone_number,
                email=user.email
            )
            stripe_customer = models.Customer.objects.create(
                user=user,
                customer_id=customer["id"]
            )

        return stripe_customer

    def update_customer(self, *kwargs):
        pass

    def retrieve_and_update_payment_intent(self, intent_id: str):
        try:
            obj = models.PaymentIntent.objects.get(intent_id=intent_id)
        except models.PaymentIntent.DoesNotExist:
            return

        payment_intent = self.stripe.PaymentIntent.retrieve(intent_id)
        obj.data = payment_intent
        obj.save()

    def create_payment_intent(
            self,
            amount,
            customer,
            payment_id,
            product_id,
            capture_method,
            currency="inr",
            payment_method_types=["card"],
            confirm=True
    ):
        intent = self.stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            customer=customer.customer_id,
            payment_method_types=payment_method_types,
            capture_method=capture_method,
            confirm=confirm
        )
        stripe_intent_object = models.PaymentIntent.objects.create(
            payment_id=payment_id,
            customer_id=customer.id,
            amount=amount / 100,
            client_secret=intent.client_secret,
            product_id=product_id,
            data=intent.to_dict(),
            intent_id=intent.id,
        )
        return stripe_intent_object

    def capture_payment_intent(self, intent, amount=None):
        try:
            updated = self.stripe.PaymentIntent.capture(
                intent.intent_id,
                amount_to_capture=amount
            )
            intent.data = updated.to_dict()
            intent.save()
            return intent

        except Exception as e:
            logging.error(
                str(e)
            )
            raise e


stripe_service = StripePaymentService(api_key=settings.STRIPE_SECRET_KEY)
