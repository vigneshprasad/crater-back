from django.contrib import admin
from django.contrib.admin import ModelAdmin, register
from django.utils.safestring import mark_safe

from locations.models import Country, City


class CityInline(admin.TabularInline):
    model = City
    fields = ('id', 'name', 'country', 'is_work')
    ordering = ('name',)
    can_delete = False
    extra = 0

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@register(Country)
class CountryAdmin(ModelAdmin):
    icon_name = 'business'
    list_display = ('name', 'cities')
    inlines = [CityInline]

    @staticmethod
    def cities(country):
        if not country.city_set.exists():
            return mark_safe('<i class="material-icons red-color medium-icon">highlight_off</i>')
        return ', '.join([city.name for city in country.city_set.all()])

    def get_queryset(self, request):
        return Country.objects.prefetch_related('city_set').all()
