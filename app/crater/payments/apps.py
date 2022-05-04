from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    name = "crater.payments"
    label = "crater_payments"

    def ready(self):
        import crater.payments.receivers
