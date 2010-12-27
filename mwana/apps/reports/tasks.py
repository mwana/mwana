# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.models import PhoReportNotification
import logging
from datetime import date
from datetime import timedelta
from mwana.apps.labresults.models import Result
from mwana.apps.reminders.models import PatientEvent
from mwana.apps.reports.models import DhoReportNotification
from mwana.const import get_district_worker_type
from mwana.const import get_province_worker_type
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact
from django.db.models import Q
logger = logging.getLogger(__name__)

EID_BIRTH_SUMMARY = "%(name)s, %(month)s %(location_name)s EID & Birth Totals\nDBS Samples sent: %(samples)s ***\nDBS Results received: %(results)s ***\nBirths registered: %(births)s"

def send_dho_eid_and_birth_report(router):
    logger.info('notifying district workers of monthly EID and Births summary')
    workers = Contact.active.filter(types=get_district_worker_type())
    if not workers:
        logger.warning('No district workers found in the system')
    today = date.today()
    month_ago = date(today.year, today.month, 1)-timedelta(days=1)
    last_year = month_ago.year
    last_month = month_ago.month
    for woker in workers:
        district = woker.location
        reports = DhoReportNotification.objects.filter(district=district,
                                                       contact=woker,
                                                       date__year=last_year,
                                                       date__month=last_month)
        if reports:
            continue
        name = woker.name
        month = month_ago.strftime("%B")
        samples = Result.objects.filter(clinic__parent=district,
                                        entered_on__year=last_year,
                                        entered_on__month=last_month).count()
        results = Result.objects.filter(clinic__parent=district,
                                        result_sent_date__year=last_year,
                                        result_sent_date__month=last_month).count()

        births = PatientEvent.objects.filter(Q(event__name__iexact='birth'),
                                             Q(cba_conn__contact__location__parent__parent=district)
                                             |Q(cba_conn__contact__location__parent=district),# cba/clinic worker
                                             Q(date__year=last_year),
                                             Q(date__month=last_month)).distinct().count()

        district_name = district.name

        msg = (EID_BIRTH_SUMMARY % {'name':name, 'month':month,
               'births':births, 'samples':samples,
               'results':results, 'location_name':district_name})

        DhoReportNotification.objects.create(contact=woker,
                                             district=woker.location, type='M',
                                             samples=samples, results=results,
                                             births=births,
                                             date=month_ago)

        OutgoingMessage(woker.default_connection, msg).send()

def send_pho_eid_and_birth_report(router):
    logger.info('notifying province workers of monthly EID and Births summary')
    workers = Contact.active.filter(types=get_province_worker_type())
    if not workers:
        logger.warning('No province workers found in the system')
    today = date.today()
    month_ago = date(today.year, today.month, 1)-timedelta(days=1)
    last_year = month_ago.year
    last_month = month_ago.month
    for woker in workers:
        province = woker.location
        reports = PhoReportNotification.objects.filter(province=province,
                                                       contact=woker,
                                                       date__year=last_year,
                                                       date__month=last_month)
        if reports:
            continue
        name = woker.name
        month = month_ago.strftime("%B")
        samples = Result.objects.filter(clinic__parent__parent=province,
                                        entered_on__year=last_year,
                                        entered_on__month=last_month).count()
        results = Result.objects.filter(clinic__parent__parent=province,
                                        result_sent_date__year=last_year,
                                        result_sent_date__month=last_month).count()

        births = PatientEvent.objects.filter(Q(event__name__iexact='birth'),
                                             Q(cba_conn__contact__location__parent__parent__parent=province)
                                             |Q(cba_conn__contact__location__parent__parent=province),# cba/clinic worker
                                             Q(date__year=last_year),
                                             Q(date__month=last_month)).distinct().count()

        province_name = province.name

        msg = (EID_BIRTH_SUMMARY % {'name':name, 'month':month,
               'births':births, 'samples':samples,
               'results':results, 'location_name':province_name})

        PhoReportNotification.objects.create(contact=woker,
                                             province=woker.location, type='M',
                                             samples=samples, results=results,
                                             births=births,
                                             date=month_ago)

        OutgoingMessage(woker.default_connection, msg).send()
