from django.apps import AppConfig


class WatiAppConfig(AppConfig):
    name = "integrations.wati"

    def ready(self):
        # import integrations.wati.receivers
        # import integrations.wati.signals
        pass
