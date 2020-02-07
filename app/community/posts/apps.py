from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class PostConfig(AppConfig):
    name = 'community.posts'
    icon_name = 'assignment'
    verbose_name = _('Post')

    def ready(self):
        import community.posts.signals
