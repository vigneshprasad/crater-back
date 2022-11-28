from django.apps import AppConfig


class SlackConfig(AppConfig):
    name = "integrations.slack"
    label = "slack"

    def ready(self):
        pass
