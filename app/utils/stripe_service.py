import stripe
from django.conf import settings

from users.models import User


class StripeService:

    def __init__(self, api_key):
        self.stripe = stripe
        self.stripe.api_key = api_key

    def get_customer_id(self, user: User, token) -> str:
        name = user.email
        if hasattr(user, 'profile') and user.profile:
            name = user.profile.name
        data = {
            'address': {
                'line1': 'Non Address Payment',
                'city': 'Non City Payment',
                'country': 'US',
            }
        }
        customer = self.stripe.Customer.create(
            source=token,
            email=user.email,
            name=name,
            **data
        )
        return customer.stripe_id

    def get_customer_card_data(self, customer_id):
        if customer_id:
            cards = self.stripe.Customer.list_sources(
                customer_id,
                # object='bank_account',
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

    def create_token_charge(self, token, amount, description, user, currency=settings.LOCAL_CURRENCY):
        name = user.email
        if hasattr(user, 'profile') and user.profile:
            name = user.profile.name
        shipping = {
            'name': name,
            'address': {
                'line1': 'Non Address Payment',
                'city': 'Non City Payment',
                'country': settings.LOCAL_COUNTRY,
            }
        }
        charge = self.stripe.Charge.create(
            amount=amount,
            currency=currency,
            description=description,
            source=token,
            shipping=shipping
        )
        return charge

    def create_customer_charge(self, customer_id, amount, description, currency=settings.LOCAL_CURRENCY):
        charge = self.stripe.Charge.create(
            amount=amount,
            currency=currency,
            description=description,
            customer=customer_id
        )
        return charge

    def create_payment_intent(self, amount, description, receipt_email, currency=settings.LOCAL_CURRENCY):
        return self.stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            payment_method_types=['card'],
            description=description,
            receipt_email=receipt_email
        )

    def retrieve_payment_intent(self, intent_id):
        return self.stripe.PaymentIntent.retrieve(intent_id)


stripe_service = StripeService(api_key=settings.STRIPE_SECRET_KEY)
