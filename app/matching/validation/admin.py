from django.contrib import admin
from django_admin_row_actions import AdminRowActionsMixin

from matching.validation import models


@admin.register(models.UserValidation)
class UserValidationAdmin(AdminRowActionsMixin, admin.ModelAdmin):
    list_display = ("user", "rule", "result", "is_validated")
    search_fields = ("user__email", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    def get_row_actions(self, obj):
        row_actions = [
            {
                "divided": True,
                "label": "Validate",
                "action": "validate",
                "enabled": obj.is_validated is False,
            },
        ]
        row_actions += super(UserValidationAdmin, self).get_row_actions(obj)
        return row_actions

    @staticmethod
    def validate(request, obj):
        if obj.is_validated:
            return
        obj.is_validated = True
        obj.save()
