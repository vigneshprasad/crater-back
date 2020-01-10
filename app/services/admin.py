from django.contrib import admin
from django.contrib.admin import ModelAdmin, register

from services.models import ServiceType, Service, UserServiceInfo, InvestorServiceInfo, \
    MarketingCategoryProxy, ProfessionalCategoryProxy
from utils.mixins import ViewActionMixin


class ServiceTypeInline(admin.TabularInline):
    model = ServiceType
    extra = 0


@register(MarketingCategoryProxy)
class MarketingCategoryAdmin(ViewActionMixin, ModelAdmin):
    """
    Service Category contains service types
    """
    icon_name = 'apps'
    list_display = ('name', 'action')
    fields = ['name', 'photo']
    inlines = [ServiceTypeInline]
    search_fields = ['name']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(direction='marketing')


@register(ProfessionalCategoryProxy)
class ProfessionalCategoryAdmin(ViewActionMixin, ModelAdmin):
    """
    Service Category contains service types
    """
    icon_name = 'apps'
    list_display = ('name', 'action')
    fields = ['name', 'photo']
    inlines = [ServiceTypeInline]
    search_fields = ['name']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(direction='professional')


@register(Service)
class ServiceAdmin(ViewActionMixin, ModelAdmin):
    """
    User Services
    """
    icon_name = 'room_service'
    list_display = ('service_type', 'status', 'user', 'action')
    list_filter = ['status']
    search_fields = ['user__email', 'service_type__name']


@register(UserServiceInfo)
class UserServiceInfoAdmin(ViewActionMixin, ModelAdmin):
    """
    User Service instance Info
    """
    icon_name = 'extension'
    list_display = (
        'user',
        'years_of_experience',
        'bar_council',
        'followers',
        'action'
    )
    readonly_fields = ['user']
    search_fields = ['user__email']

    def has_add_permission(self, request):
        return False


@register(InvestorServiceInfo)
class InvestorServiceInfoAdmin(ViewActionMixin, ModelAdmin):
    """
    Investor Service instance Info
    """
    icon_name = 'extension'
    list_display = (
        'user',
        'years_of_experience',
        'number_of_startups',
        'connect_with_us',
        'process',
        'action'
    )
    readonly_fields = ['user']
    search_fields = ['user__email']

    def has_add_permission(self, request):
        return False
