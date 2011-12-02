# vim: ai ts=4 sts=4 et sw=4
from datetime import date
import logging

from django.db.models import Count
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact
logger = logging.getLogger(__name__)

EID_BIRTH_SUMMARY = "%(name)s, %(month)s %(location_name)s EID & Birth Totals\nDBS Samples sent: %(samples)s ***\nDBS Results received: %(results)s ***\nBirths registered: %(births)s"
CBA_THANKS_MSG = "Thank you, %(name)s. You have helped about %(helps)s mothers in your community in %(month)s %(year)s. Keep up the good work, reminding mothers saves lives."
CBA_REMINDER_MSG = "Hello %(name)s. Remember to register births in your community and to remind mothers go to the clinic. Reminding mothers saves lives."

def year():
    return date.today().year

def month():
    return date.today().month

def day():
    return date.today().day

def get_payload_data():
    p = Payload.objects.filter(incoming_date__year=year(),
                               incoming_date__month=month(),
                               incoming_date__day=day()).\
        values("source").annotate(Count('id'))
    return "\n".join(entry['source'] + ": " + str(entry['id__count']) for entry in p)

def get_results_data():
    sent_today = Result.objects.filter(notification_status='sent',
                                       result_sent_date__year=year(),
                                       result_sent_date__month=month(),
                                       result_sent_date__day=day()
                                       ).count()
    new = Result.objects.filter(notification_status='new').count()
    notified = Result.objects.filter(notification_status='new').count()

    return "New: %s\nNotified: %s\nSent: %s" % (new, notified, sent_today,)

def send_monitor_report(router):
    logger.info('sending monitoring information to support staff')

    # TODO : move setting of recipients to database table
    admins = Contact.active.filter(is_help_admin=True,
                                   name__icontains="Trevor Sinkala",
                                   connection__identity__icontains="096")

    if not admins:
        logger.warning('No admins to send monitoring data to were found in system')
        return
    message = "Payloads:\n%s;\nResults:\n%s" % (get_payload_data(), get_results_data())

    
    for admin in admins:
        OutgoingMessage(admin.default_connection, message).send()

