# vim: ai ts=4 sts=4 et sw=4
"""
Updates Alerts Reporting table  - clinics_not_sending_dbs
"""

from mwana.apps.labresults.models import Payload
from mwana.const import get_dbs_printer_type
from mwana.const import get_clinic_worker_type
from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message
from datetime import date
from django.core.management.base import LabelCommand
from mwana.apps.alerts.labresultsalerts.alerter import Alerter
from mwana.apps.locations.models import Location
from mwana.apps.reports.models import ClinicsNotSendingDBS
from mwana import const
from mwana.apps.labresults.handlers.results import ResultsHandler

class Command(LabelCommand):
    help = "Updates clinics_not_sending_dbs reporting table"
   

    def handle(self, * args, ** options):
        update_clinics_not_sending_dbs()

def __del__(self):
    pass

def _days_ago(p_date):
    if p_date == date(1900, 1, 1):
        return None
    return (date.today() - p_date).days


result_keyword_msgs = Message.objects.filter(direction='I',
                                text__iregex=r'^(%s)|^result$' % '|'.join(
                                '%s ' %it for it in ResultsHandler.keyword.\
                                strip().split('|')))

def update_clinics_not_sending_dbs():
    locs = Location.objects.filter(supportedlocation__supported=True)
    alerter = Alerter()
    alerter.set_tracing_start(365 * (date.today().year - 2010))# include all days system has been running
    try:
        last_msg = Message.objects.filter(contact__types__in=[get_clinic_worker_type(), get_dbs_printer_type()], direction='I').order_by('-date')[0].date
        last_mod = ClinicsNotSendingDBS.objects.all().order_by('-last_modified')[0].last_modified
        last_payload = Payload.objects.all().order_by('incoming_date')[0].incoming_date
        #Check if there is no need to update
        if last_mod > last_msg and last_mod > last_payload:
            return

    except IndexError:
        #Do nothing. Run rest of function
        pass

    for location in locs:
        obj, _ = ClinicsNotSendingDBS.objects.get_or_create(location=location)
        obj.last_sent_samples = _days_ago(alerter.last_sent_samples(location))
        obj.last_retrieved_results = _days_ago(alerter.last_retrieved_results(location))
        obj.last_used_sent = _days_ago(alerter.last_used_sent(location))
        obj.last_used_check = _days_ago(alerter.last_used_check(location))
        obj.last_used_result = _days_ago(alerter._last_used_result(location, result_keyword_msgs))
        obj.last_used_trace = _days_ago(alerter.get_last_used_trace(location))
        contacts = Contact.active.filter(location=location, types=const.get_clinic_worker_type()
                                         ).distinct().order_by('name')
        obj.contacts = ", ".join(contact.name + ":"
                                 + contact.default_connection.identity
                                 for contact in contacts)        
        obj.save()



