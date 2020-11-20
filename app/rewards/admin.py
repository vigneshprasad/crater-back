from django.contrib.admin import register, ModelAdmin

from rewards import models


@register(models.PackageProvider)
class PackageProviderAdmin(ModelAdmin):
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')
    list_display = (
        'user',
        'name',
    )


@register(models.Package)
class PackageAdmin(ModelAdmin):
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')
    list_display = (
        'title',
        'max_price',
        'max_discount',
        'provider',
    )


@register(models.PackageRequest)
class PackageRequestAdmin(ModelAdmin):
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')
    readonly_fields = [
        'payable_amount'
    ]
    list_display = (
        'requested_by',
        'package',
        'point_applied',
        'status',
    )

    @staticmethod
    def payable_amount(self):
        return self.package.max_price * self.quantity - (self.point_applied * self.package.points_conversion)
