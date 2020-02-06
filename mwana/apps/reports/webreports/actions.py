import csv
from django.http import HttpResponse

def export_as_csv_action(description="Export selected objects as CSV file",
                         fields=None, exclude=None, header=True):
    """
    This function returns an export csv action
    'fields' and 'exclude' work like in django ModelForm
    'header' is whether or not to output the column names as the first row
    """
    def export_as_csv(modeladmin, request, queryset):
        opts = modeladmin.model._meta

        if not fields:
            field_names = [field.name for field in opts.fields]
        else:
            field_names = fields
        field_names = list(field_names)
        if exclude:
            for field in exclude:
                if field in field_names:
                    field_names.remove(field)

        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % unicode(opts).replace('.', '_')

        writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if header:
            writer.writerow(field_names)
        for obj in queryset:
            row = [getattr(obj, field)() if callable(getattr(obj, field)) else getattr(obj, field) for field in field_names]
            writer.writerow([("%s" % x).encode('utf-8') for x in row])
        return response
    export_as_csv.short_description = description
    return export_as_csv