from django.apps import AppConfig


class TagsConfig(AppConfig):
    name = 'tags'
    icon_name = 'label'

    def ready(self):
        import tags.signals
        import tags.receivers
