from django.apps import AppConfig


class AuctionsConfig(AppConfig):
    name = "crater.auctions"
    label = "auctions"

    def ready(self):
        import crater.auctions.signals
        import crater.auctions.receivers
