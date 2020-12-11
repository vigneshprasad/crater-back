from django.contrib import admin
from django.contrib.admin import register

from matching import models


@register(models.UserScore)
class UserScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score')
    search_fields = ('user__email', )
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted', 'score_breakdown', 'score_weightages')


@register(models.UserToUserMatchScore)
class UserToUserMatchScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'matched_user', 'score')
    search_fields = ('user__email',)
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')
