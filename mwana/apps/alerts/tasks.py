# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.alerts.labresultsalerts.alert import Alert
from datetime import date
from datetime import datetime
from datetime import timedelta
import logging

from mwana.apps.alerts.labresultsalerts.alert import Alert
from mwana.apps.alerts.models import DhoSMSAlertNotification
from mwana.apps.alerts.models import Hub
from mwana.apps.labresults.models import Payload
from mwana.apps.locations.models import Location
from mwana.const import get_district_worker_type
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact

logger = logging.getLogger(__name__)


RETRIEVING_DAYS = 3
CLINIC_NOTIFICATION_DAYS = 14
DISTICT_TRANSPORT_DAYS = 12

def init_varibles():
    global dhos
    global today
    global yesterday
   
    dhos = Contact.active.filter(types=get_district_worker_type(), location__smsalertlocation__enabled=True)
    logger.info('%s DHOs eligible for SMS alerts' % dhos.count())

    today = date.today()
    yesterday = datetime(today.year, today.month, today.day)-timedelta(days=1)

def get_lab_name(district):
    try:
        return Payload.objects.filter(lab_results__clinic__parent\
                                      =district)[0].source.title()
    except Payload.DoesNotExist:
        return "(Unkown lab)"

def send_clinics_not_retrieving_results_alerts(router):
    logger.info('notifying DHOs of clinics not retrieving results')
    init_varibles()

    retrieving_ref_date = \
    datetime(today.year, today.month, today.day)-timedelta(days=RETRIEVING_DAYS)
    

    for dho in dhos:
        my_clinics = Location.objects.filter(parent=dho.location,
                                             lab_results__notification_status='notified',
                                             lab_results__arrival_date__lt=retrieving_ref_date
                                             ).distinct()[:5]
        if not my_clinics:
            continue
        msg = "ALERT! %s, Clinics haven't retrieved results: %s" % (dho.name, ", ".\
                                                                    join(clinic.name for clinic in my_clinics))

        process_msg_for_dho(dho, "W", Alert.LONG_PENDING_RESULTS, yesterday, msg)
        
       

def send_clinics_not_sending_dbs_alerts(router):
    logger.info('notifying DHOs of clinics not sending DBS samples to hub')
    init_varibles()

    clinic_sent_dbs_referal_date = \
    datetime(today.year, today.month, today.day)-timedelta(days=CLINIC_NOTIFICATION_DAYS)

    for dho in dhos:
        facs = get_active_facilities().filter(parent=dho.location)
        my_clinics = facs.\
            exclude(lab_results__entered_on__gte=
                    clinic_sent_dbs_referal_date.date()).\
                exclude(samplenotification__date__gte=
                        clinic_sent_dbs_referal_date.date()).distinct()[:5]
        
        if not my_clinics:
            continue
        
        msg = "ALERT! %s, Clinics haven't sent DBS to hub: %s" % (dho.name, ", ".\
                                                                  join(clinic.name for clinic in my_clinics))
        process_msg_for_dho(dho, "W", Alert.CLINIC_NOT_USING_SYSTEM, yesterday, msg)
        
def send_hubs_not_sending_dbs_alerts(router):
    logger.info('notifying DHOs of district hubs not sending DBS samples to lab')
    init_varibles()

    hub_sent_dbs_referal_date = \
    date(today.year, today.month, today.day)-timedelta(days=DISTICT_TRANSPORT_DAYS)

    for dho in dhos:
        try:
            last_retrieved = Result.objects.filter(clinic__parent=location).exclude(result_sent_date=None).order_by("-result_sent_date")[0].result_sent_date.date()
        except:
            last_retrieved = date(1900, 1, 1)
        if last_retrieved >= hub_sent_dbs_referal_date:
            continue     
        dist = dho.location
        msg = ("The %s district hub (%s) has not "
               "sent samples to %s in over %s "
               "days." %
               (dist.name,
               get_hub_name(dist),
               get_lab_name(dist),
               DISTICT_TRANSPORT_DAYS-1)
               )
        process_msg_for_dho(dho, "W", Alert.DISTRICT_NOT_SENDING_DBS, yesterday, msg)

def process_msg_for_dho(contact, report_type, alert_type, date_back, msg):

    old_msg = DhoSMSAlertNotification.objects.filter(contact=contact,
                                                     report_type=report_type,
                                                     alert_type=alert_type,
                                                     district=contact.location,
                                                     date_sent__gte=date_back)
    if old_msg:
        logger.info('%s already notiffied of alert (%s)' % (contact.name, alert_type))
        return

    OutgoingMessage(contact.default_connection, msg).send()
    DhoSMSAlertNotification.objects.create(contact=contact, report_type=report_type,
                                           alert_type=alert_type,
                                           district=contact.location)

def get_active_facilities():
    return Location.objects.filter(lab_results__notification_status__in=
                                   ['sent']).distinct()
def get_hub_name(location):
    try:
        return Location.objects.filter(contact__types=get_hub_worker_type()).distinct().get(parent=location).name
    except:
        try:
            return Hub.objects.get(district=location).name
        except Hub.DoesNotExist:
            return "Unkown hub"

def get_lab_name(district):
    try:
        return Payload.objects.filter(lab_results__clinic__parent\
                                      =district)[0].source
    except:
        return "Unkown lab"