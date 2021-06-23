from django.contrib import admin

from devices import models


@admin.register(models.Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "model", "price")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
