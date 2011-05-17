# vim: ai ts=4 sts=4 et sw=4
import logging
from datetime import date
from datetime import timedelta
from mwana.apps.hub_workflow.models import HubReportNotification
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from mwana.const import get_hub_worker_type
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact
logger = logging.getLogger(__name__)

SAMPLES_RECEIVED_TODAY = "Hello %(name)s. %(lab_name)s lab has received %(count)s samples from %(hub_name)s hub this week."
DBS_SUMMARY = "Hello %(name)s. In %(month)s, %(hub_name)s hub sent %(samples)s DBS samples to the lab and %(results)s DBS results were delivered to %(district_name)s District"

def get_lab_name(district):
    try:
        return Payload.objects.filter(lab_results__clinic__parent\
                                      =district)[0].source.title()
    except Payload.DoesNotExist:
        return "(Unkown lab)"

def send_new_dbs_at_lab_notification(router):
    logger.info('notifying hub workers of new DBS entered today at lab')
    hub_workers = Contact.active.filter(types=get_hub_worker_type())
    today = date.today()
    weekstart = today -timedelta(days =(today.weekday()+1))
    for hub_woker in hub_workers:
        district = hub_woker.location.parent
        samples = Result.objects.filter(entered_on__gte=weekstart, clinic__parent=district).count()
        if not samples:
            continue
        my_lab = get_lab_name(district)
        msg = (SAMPLES_RECEIVED_TODAY % {'name':hub_woker.name, 'lab_name':my_lab,
               'count':samples, 'hub_name':hub_woker.location.name})
        OutgoingMessage(hub_woker.default_connection, msg).send()

def send_dbs_summary_to_hub_report(router):
    logger.info('notifying hub workers of monthly DBS summary')
    hub_workers = Contact.active.filter(types=get_hub_worker_type())
    if not hub_workers:
        logger.warning('No hub workers found in the system')
        return
    today = date.today()
    month_ago = date(today.year, today.month, 1)-timedelta(days=1)
    last_year = month_ago.year
    last_month = month_ago.month
    for hub_woker in hub_workers:
        district = hub_woker.location.parent
        reports = HubReportNotification.objects.filter(lab__parent=district,
                                                       contact=hub_woker,
                                                       date__year=last_year,
                                                       date__month=last_month)
        if reports:
            continue
        name = hub_woker.name
        month = month_ago.strftime("%B")
        hub_name = hub_woker.location.name
        samples = Result.objects.filter(clinic__parent=hub_woker.location.parent,
                                        entered_on__year=last_year,
                                        entered_on__month=last_month).count()
        results = Result.objects.filter(clinic__parent=hub_woker.location.parent,
                                        result_sent_date__year=last_year,
                                        result_sent_date__month=last_month).count()
        district_name = district.name

        msg = (DBS_SUMMARY % {'name':name, 'month':month,
               'hub_name':hub_name, 'samples':samples,
               'results':results, 'district_name':district_name})

        HubReportNotification.objects.create(contact=hub_woker,
                                             lab=hub_woker.location, type='M',
                                             samples=samples, results=results,
                                             date=month_ago)
        OutgoingMessage(hub_woker.default_connection, msg).send()
