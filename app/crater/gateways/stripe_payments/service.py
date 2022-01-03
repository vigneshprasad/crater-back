import stripe

from django.conf import settings

from crater.gateways.stripe_payments import models


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

        return stripe_customer.customer_id


    def update_customer(self, *kwargs):
        pass

    def create_payment_intent(self, amount):
        pass


stripe_test_service = StripePaymentService(api_key=settings.STRIPE_SECRET_KEY)
