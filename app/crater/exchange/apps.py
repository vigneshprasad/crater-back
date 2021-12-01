from django.apps import AppConfig


class ExchangeConfig(AppConfig):
    name = "crater.exchange"
    label = "crater_exchange"

    def ready(self):
        pass
