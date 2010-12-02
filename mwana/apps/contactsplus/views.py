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
    headings = ['Name', 'Phone', 'District', 'Facility', 'Facility Type',
                'Registered', 'Contact Type']
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
        earliest = Message.objects.filter(
            contact=obj.id,
            direction='I',
        ).aggregate(registered=Min('date'))
        row.append(earliest['registered'])
        row.append(";".join(obj.types.values_list('name', flat=True)))
        row = [unicode(v).encode("UTF-8") for v in row]
        writer.writerow(row)
    return response
