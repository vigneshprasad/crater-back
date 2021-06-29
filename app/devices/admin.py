from django.contrib import admin

from devices import models


@admin.register(models.Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "model", "price")
    search_fields = ("name", "model")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ("user", "device_name", "device_model", "device_price", "last_used")
    search_fields = ("user__email", "device__name", "device__model")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    @staticmethod
    def device_name(obj):
        return obj.device.name

    @staticmethod
    def device_model(obj):
        return obj.device.model

    @staticmethod
    def device_price(obj):
        return obj.device.price
