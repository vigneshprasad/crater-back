from django.apps import AppConfig


class RewardsConfig(AppConfig):
    name = 'rewards'
    icon_name = 'local_offer'

    def ready(self):
        import rewards.receivers
