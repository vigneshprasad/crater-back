from django.contrib import admin
from django.contrib.admin import register

from tags.models import Tag


@register(Tag)
class TagAdmin(admin.ModelAdmin):
    icon_name = 'label'
