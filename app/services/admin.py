from django.contrib import admin
from django.contrib.admin import ModelAdmin, register

from services.models import Category, ServiceType, Service
from utils.mixins import ViewActionMixin


class ServiceTypeInline(admin.TabularInline):
    model = ServiceType
    extra = 0


@register(Category)
class CategoryAdmin(ViewActionMixin, ModelAdmin):
    icon_name = 'apps'
    list_display = ('name', 'action')
    inlines = [ServiceTypeInline]
    search_fields = ['name']


@register(Service)
class ServiceAdmin(ViewActionMixin, ModelAdmin):
    icon_name = 'room_service'
    list_display = ('service_type', 'status', 'user', 'action')
    list_filter = ['status']
    search_fields = ['user__email', 'service_type__name']

