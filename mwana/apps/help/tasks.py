import csv
import StringIO
import logging
from datetime import date, timedelta

from celery import task

from django.core.mail.message import EmailMessage
from django.utils.encoding import smart_str

from mwana.apps.help.models import HelpRequest

logger = logging.getLogger('mwana.apps.help.tasks')

HELP_REQUEST_ADMINS = ['lengani@gmail.com']


def parent_loc(obj):
    try:
        return obj.requested_by.contact.location.parent.name
    except:
        return "Unknown"


def location(obj):
    try:
        return obj.requested_by.contact.location.name
    except:
        return "Unknown"


def type(obj):
    try:
        return ";".join(type.name for type in obj.requested_by.contact.types.all())
    except:
        return ""


def name(obj):
    try:
        return obj.requested_by.contact.name
    except:
        return ""


@task
def export_help_requests(recipients=HELP_REQUEST_ADMINS, days=None,):
    enddate = date.today()
    if days is not None:
        startdate = enddate - timedelta(days=days)
    else:
        startdate = enddate - timedelta(days=1)
    file_name = str(startdate) + "_" + str(enddate)
    headers = [u"Parent Location", u"Location",
               u"Requested By", u"Contact Number",
               u"Role", u"Requested on", u"Additional Text", u"Status"]
    help_requests = HelpRequest.objects.filter(
        requested_on__gte=startdate,
        requested_on__lte=enddate)
    csvfile = StringIO.StringIO()
    writer = csv.writer(csvfile, csv.excel)
    writer.writerow([smart_str(hdr) for hdr in headers])
    for obj in help_requests:
        if obj.requested_by.contact is not None:
            fields = [parent_loc(obj), location(obj),
                      obj.requested_by.contact.name,
                      obj.requested_by, type(obj), obj.requested_on,
                      obj.additional_text, obj.get_status_display()]
            writer.writerow([smart_str(field_value) for field_value in fields])

    email = EmailMessage()
    email.subject = "Help Requests from " + str(startdate)\
                    + "to " + str(enddate)
    email.body = "Hello,\nPlease find attached the help requests from " +\
                 str(startdate) + " to " + str(enddate) + "."
    email.from_email = "Mwana Production <no-reply@malawi-qa.projectmwana.org>"
    email.attach(file_name, csvfile.getvalue(), 'text/csv')
    fout = open('%s.csv' % file_name, 'w')
    fout.write(csvfile.getvalue())
    fout.close()
    email.send()
