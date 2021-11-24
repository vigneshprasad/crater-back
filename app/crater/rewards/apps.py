from django.apps import AppConfig


class CraterRewardsConfig(AppConfig):
    name = "crater.rewards"
    label = "crater_rewards"

    def ready(self):
        pass
