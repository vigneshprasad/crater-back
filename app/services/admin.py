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
    list_display = ('name', 'services_inside', 'action')
    fields = ['name', 'photo']
    inlines = [ServiceTypeInline]
    search_fields = ['name']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(direction='marketing')

    def services_inside(self, category):
        return category.service_types.count()
    services_inside.allow_tags = True
    services_inside.short_description = 'services inside'


@register(ProfessionalCategoryProxy)
class ProfessionalCategoryAdmin(ViewActionMixin, ModelAdmin):
    """
    Service Category contains service types
    """
    icon_name = 'apps'
    list_display = ('name', 'services_inside', 'action')
    fields = ['name', 'photo']
    inlines = [ServiceTypeInline]
    search_fields = ['name']

    def services_inside(self, category):
        return category.service_types.count()
    services_inside.allow_tags = True
    services_inside.short_description = 'services'

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
    readonly_fields = (
        'user', 'service_type', 'price_type', 'price', 'timeline', 'revision', 'includes', 'attachments', 'questions',
        'rating'
    )

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'service_type')


@register(ServiceType)
class ServiceTypeAdmin(ViewActionMixin, ModelAdmin):
    """
    User Service Types
    """
    icon_name = 'room_service'
    list_display = ('category', 'group', 'providers', 'action')
    list_filter = ['group']
    search_fields = ['category']

    def providers(self, service_type):
        return service_type.services.count()
    providers.allow_tags = True
    providers.short_description = 'providers'


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
