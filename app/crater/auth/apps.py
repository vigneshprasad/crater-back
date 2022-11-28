from django.apps import AppConfig


class AuthConfig(AppConfig):
    name = "crater.auth"
    label = "crater_auth"

    def ready(self):
        import crater.auth.receivers
        import crater.auth.signals
