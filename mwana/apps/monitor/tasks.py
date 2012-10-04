# vim: ai ts=4 sts=4 et sw=4
from datetime import date
import logging

from django.db.models import Count
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact
logger = logging.getLogger(__name__)


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
    notified = Result.objects.filter(notification_status='notified').count()

    return "New: %s\nNotified: %s\nSent: %s" % (new, notified, sent_today,)

def send_monitor_report(router):
    logger.info('sending monitoring information to support staff')

    
    admins = Contact.active.filter(is_help_admin=True,
                                   monitormessagerecipient__receive_sms=True)

    if not admins:
        logger.warning('No admins to send monitoring data to were found in system')
        return
    message = "System message.\nPayloads:\n%s;\nResults:\n%s" % (get_payload_data(), get_results_data())

    
    for admin in admins:
        OutgoingMessage(admin.default_connection, message).send()

