from django.apps import AppConfig


class ServicesConfig(AppConfig):
    name = 'services'
    icon_name = 'room_service'

    def ready(self):
        pass
