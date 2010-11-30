import csv
from django.http import HttpResponse
from django.db.models import Min
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message


@login_required
def export_contacts(request):
    contacts = Contact.objects.all().order_by('name')
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment;filename=contacts_export.csv'
    writer = csv.writer(response)
    headings = ['Name', 'Phone','District','Facility', 'Type', 'Registered']
    writer.writerow(headings)
    for obj in contacts:
        row = []
        row.append(obj.name)
        if obj.default_connection is not None:
            phone = obj.default_connection.identity
        else:
            phone = 'Not available'
        row.append(phone)
        row.append(obj.location.parent)
        row.append(obj.location)
        row.append(obj.location.type)
        #row.append()
        earliest = Message.objects.filter(contact=obj.id, direction='I').aggregate(registered=Min('date'))
        row.append(earliest['registered'])
        writer.writerow(row)
    return response
    
def export_to_csv(modeladmin, request, queryset):
    """
    Generic csv export admin action.
    """
    if not request.user.is_staff:
        raise PermissionDenied
    opts = modeladmin.model._meta
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % unicode(opts).replace('.', '_')
    writer = csv.writer(response)
    field_names = [field.name for field in opts.fields]
    # Write a first row with header information
    writer.writerow(field_names)
    # Write data rows
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])
    return response
