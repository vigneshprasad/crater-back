from django.apps import AppConfig


class CraterSearchConfig(AppConfig):
    name = "crater.search"
    label = "crater_search"

    def ready(self):
        pass
