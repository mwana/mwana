# vim: ai ts=4 sts=4 et sw=4
import csv
from django.http import HttpResponse
from django.db.models import Min
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message


@login_required
def export_contacts(request):
    contacts = Contact.active.all()
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment;filename=contacts_export.csv'
    writer = csv.writer(response)
    headings = ['Name', 'Phone', 'District', 'Facility',  
                'Registered', 'Contact Type']
    writer.writerow(headings)
    for obj in contacts:
        row = []
        row.append(obj.name)
        if obj.default_connection is not None:
            row.append(obj.default_connection.identity)
        else:
            row.append('No number')
        row.append(obj.district)
        row.append(obj.clinic)
        earliest = Message.objects.filter(
            contact=obj.id,
            direction='I',
        ).aggregate(registered=Min('date'))
        row.append(earliest['registered'])
        row.append(";".join(obj.types.values_list('name', flat=True)))
        row = [unicode(v).encode("UTF-8") for v in row]
        writer.writerow(row)
    return response
