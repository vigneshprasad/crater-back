from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CuratedArticleConfig(AppConfig):
    name = 'resources.curated_articles'
    icon_name = 'local_library'
    verbose_name = _('Curated Articles')
