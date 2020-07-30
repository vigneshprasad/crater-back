import csv

from django.http import HttpResponse
from itertools import chain

from idna import unicode


# TODO(Nishant): Make this function's output readable.
def export_as_csv_action(
        description="Export selected rows",
        fields=None,
        exclude=None,
        header=True
):
    """
    This function returns an export csv action
    'fields' and 'exclude' work like in django ModelForm
    'header' is whether or not to output the column names as the first row
    """

    def export_as_csv(modeladmin, request, queryset):

        opts = modeladmin.model._meta

        field_names = set([field.name for field in opts.fields])
        many_to_many_field_names = set([
            many_to_many_field.name for many_to_many_field in opts.many_to_many
        ])

        if fields:
            field_set = set(fields)
            field_names = field_names & field_set
        elif exclude:
            exclude_set = set(exclude)
            field_names = field_names - exclude_set

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % \
                                          unicode(opts).replace('.', '_')

        writer = csv.writer(response)

        if header:
            writer.writerow(list(chain(field_names, many_to_many_field_names)))

        for obj in queryset:
            row = []
            for field in field_names:
                row.append(unicode(getattr(obj, field)))
            for field in many_to_many_field_names:
                row.append(unicode(getattr(obj, field).all()))

            writer.writerow(row)
        return response

    export_as_csv.short_description = description
    return export_as_csv
