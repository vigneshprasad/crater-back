from django.apps import AppConfig


class CreatorConfig(AppConfig):
    name = "crater.creator"
    label = "creator"

    def ready(self):
        import crater.creator.signals
        import crater.creator.receivers
