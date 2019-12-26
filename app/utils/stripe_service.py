import stripe
from django.conf import settings

from users.models import User


class StripeService:

    def __init__(self, api_key):
        self.stripe = stripe
        self.stripe.api_key = api_key

    def get_customer_id(self, user: User, token) -> str:
        customer = self.stripe.Customer.create(
            source=token,
            email=user.email,
            name=user.name
        )
        return customer.stripe_id

    def get_customer_card_data(self, customer_id):
        if customer_id:
            cards = self.stripe.Customer.list_sources(
                customer_id,
                object='bank_account',
                limit=1,
            )
            if cards.data:
                return cards.data[0]
        return None

    def update_customer_source(self, customer_id, token):
        self.stripe.Customer.modify(
            customer_id,
            source=token
        )


stripe_service = StripeService(api_key=settings.STRIPE_API_KEY)
