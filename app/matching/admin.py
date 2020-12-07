from django.contrib import admin
from django.contrib.admin import register

from matching import models


@register(models.MatchScore)
class BankDetailsAdmin(admin.ModelAdmin):
    list_display = ('user', 'score')
