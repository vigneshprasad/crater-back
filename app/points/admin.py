from django.contrib.admin import register, ModelAdmin
from .models import UserPoints, PointsLog, PointsRule


@register(UserPoints)
class UserPointsAdmin(ModelAdmin):
    list_display = ('user', 'points')
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')


@register(PointsLog)
class PointsLogAdmin(ModelAdmin):
    list_display = (
        'user',
        'action',
        'base_points_value',
        'created_at'
    )
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')
    search_fields = ['user']


@register(PointsRule)
class PointsRuleAdmin(ModelAdmin):
    list_display = (
        'key',
        'desc',
        'points_value',
    )
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')
    search_fields = ['desc']
    ordering=['key']