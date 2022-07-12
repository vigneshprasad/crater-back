from django.contrib import admin

# Register your models here.
from tokens.learn import models


@admin.register(models.LearnDailyTokenAllocation)
class LearnDailyTokenAllocationAdmin(admin.ModelAdmin):
    list_display = ("id", "amount", "date")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.LearnToken)
class LearnTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "token_log", "amount", "date", "type")
    raw_id_fields = ("user", "token_log", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
