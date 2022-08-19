from django.apps import AppConfig


class SalesConfig(AppConfig):
    name = "crater.sales"
    label = "sales"

    def ready(self):
        import crater.sales.signals
        # import crater.auctions.receivers
