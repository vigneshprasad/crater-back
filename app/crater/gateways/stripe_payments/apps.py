from django.apps import AppConfig


class StripePaymentsConfig(AppConfig):
    name = "crater.gateways.stripe_payments"
    label = "stripe_payments"

    def ready(self):
        import crater.gateways.stripe_payments.signals
        import crater.gateways.stripe_payments.receivers