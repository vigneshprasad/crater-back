import csv

from django.http import HttpResponse


class ExportCsvMixin:
    """Export to CSV for admin mixin."""
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        # TODO(Nishant): See how we can make it flow from the exclude list on admin.
        exclude_fields = ["created_at", "deleted_at", "updated_at", "is_deleted"]
        field_names = list(set(field_names) - set(exclude_fields))

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename={}.csv".format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export To CSV"
