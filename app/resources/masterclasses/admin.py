from django.contrib.admin import ModelAdmin, register

from resources.masterclasses.models import MasterClass


@register(MasterClass)
class MasterClassAdmin(ModelAdmin):
    icon_name = 'videocam'
