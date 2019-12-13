from django.contrib import admin
from django.contrib.admin import ModelAdmin, register
from django.utils.safestring import mark_safe

from locations.models import Country, City


class CityInline(admin.TabularInline):
    model = City
    ordering = ('name',)
    extra = 0


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
