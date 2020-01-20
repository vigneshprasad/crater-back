from django.contrib.admin import ModelAdmin, register
from django.utils.safestring import mark_safe

from resources.masterclasses.forms import MasterClassForm
from resources.masterclasses.models import MasterClass
from utils.mixins import ViewActionMixin


@register(MasterClass)
class MasterClassAdmin(ViewActionMixin, ModelAdmin):
    icon_name = 'videocam'
    form = MasterClassForm
    list_display = ('description', 'created', 'author', 'count', '_tags', 'action')

    @staticmethod
    def _tags(masterclass):
        return mark_safe(' '.join([
            '<span class="new badge" data-badge-caption="{}"></span>'.format(tag.name) for tag in masterclass.tags.all()
        ]))
