from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CommentConfig(AppConfig):
    name = 'community.comments'
    icon_name = 'assignment'
    verbose_name = _('Comment')

    def ready(self):
        import community.comments.receivers
        import community.comments.signals
