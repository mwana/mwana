# vim: ai ts=4 sts=4 et sw=4
from datetime import date
from datetime import timedelta
import logging
from django.conf import settings

from django.db.models import Q
from mwana.apps.labresults.models import Result
from mwana.apps.patienttracing.models import PatientTrace
from mwana.apps.reminders.models import PatientEvent
from mwana.apps.reports.models import CbaEncouragement
from mwana.apps.reports.models import CbaThanksNotification
from mwana.apps.reports.models import DhoReportNotification
from mwana.apps.reports.models import PhoReportNotification
from mwana.const import get_cba_type
from mwana.const import get_district_worker_type
from mwana.const import get_province_worker_type
from mwana.util import get_clinic_or_default
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact
logger = logging.getLogger(__name__)
_ = lambda s: s

_ = lambda s: s

EID_BIRTH_SUMMARY = "%(name)s, %(month)s %(location_name)s EID & Birth Totals\nDBS Samples sent: %(samples)s ***\nDBS Results received: %(results)s ***\nBirths registered: %(births)s"
CBA_THANKS_MSG = _("Thank you, %(name)s. You have helped about %(helps)s mothers in your community in %(month)s %(year)s. Keep up the good work, reminding mothers saves lives.")
CBA_REMINDER_MSG = _("Hello %(name)s. Remember to register births in your community and to remind mothers go to the clinic. Reminding mothers saves lives.")

def send_dho_eid_and_birth_report(router):
    logger.info('notifying district workers of monthly EID and Births summary')
    workers = Contact.active.filter(types=get_district_worker_type())
    if not workers:
        logger.warning('No district workers found in the system')
        return
    today = date.today()
    month_ago = date(today.year, today.month, 1)-timedelta(days=1)
    last_year = month_ago.year
    last_month = month_ago.month
    for worker in workers:
        district = worker.location
        reports = DhoReportNotification.objects.filter(district=district,
                                                       contact=worker,
                                                       date__year=last_year,
                                                       date__month=last_month)
        if reports:
            continue
        name = worker.name
        month = month_ago.strftime("%B")
        samples = Result.objects.filter(clinic__parent=district,
                                        entered_on__year=last_year,
                                        entered_on__month=last_month).count()
        results = Result.objects.filter(clinic__parent=district,
                                        result_sent_date__year=last_year,
                                        result_sent_date__month=last_month).count()

        births = PatientEvent.objects.filter(Q(event__name__iexact='birth'),
                                             Q(cba_conn__contact__location__parent__parent=district)
                                             | Q(cba_conn__contact__location__parent=district), # cba/clinic worker
                                             Q(date__year=last_year),
                                             Q(date__month=last_month)).distinct().count()

        district_name = district.name

        msg = (EID_BIRTH_SUMMARY % {'name':name, 'month':month,
               'births':births, 'samples':samples,
               'results':results, 'location_name':district_name})

        DhoReportNotification.objects.create(contact=worker,
                                             district=worker.location, type='M',
                                             samples=samples, results=results,
                                             births=births,
                                             date=month_ago)

        OutgoingMessage(worker.default_connection, msg).send()

def send_pho_eid_and_birth_report(router):
    logger.info('notifying province workers of monthly EID and Births summary')
    workers = Contact.active.filter(types=get_province_worker_type())
    if not workers:
        logger.warning('No province workers found in the system')
        return
    today = date.today()
    month_ago = date(today.year, today.month, 1)-timedelta(days=1)
    last_year = month_ago.year
    last_month = month_ago.month
    for worker in workers:
        province = worker.location
        reports = PhoReportNotification.objects.filter(province=province,
                                                       contact=worker,
                                                       date__year=last_year,
                                                       date__month=last_month)
        if reports:
            continue
        name = worker.name
        month = month_ago.strftime("%B")
        samples = Result.objects.filter(clinic__parent__parent=province,
                                        entered_on__year=last_year,
                                        entered_on__month=last_month).count()
        results = Result.objects.filter(clinic__parent__parent=province,
                                        result_sent_date__year=last_year,
                                        result_sent_date__month=last_month).count()

        births = PatientEvent.objects.filter(Q(event__name__iexact='birth'),
                                             Q(cba_conn__contact__location__parent__parent__parent=province)
                                             | Q(cba_conn__contact__location__parent__parent=province), # cba/clinic worker
                                             Q(date__year=last_year),
                                             Q(date__month=last_month)).distinct().count()

        province_name = province.name

        msg = (EID_BIRTH_SUMMARY % {'name':name, 'month':month,
               'births':births, 'samples':samples,
               'results':results, 'location_name':province_name})

        PhoReportNotification.objects.create(contact=worker,
                                             province=worker.location, type='M',
                                             samples=samples, results=results,
                                             births=births,
                                             date=month_ago)

        OutgoingMessage(worker.default_connection, msg).send()

def send_cba_birth_report(router):
    logger.info('thanking and notifying CBAs of monthly Births they registered')
    workers = Contact.active.filter(types=get_cba_type())
    if not workers:
        logger.warning('No CBAs found in the system')
        return
    today = date.today()
    month_ago = date(today.year, today.month, 1)-timedelta(days=1)
    last_year = month_ago.year
    last_month = month_ago.month

    counter = 0
    msg_limit = 9
    for worker in workers:
        location = get_clinic_or_default(worker)
        reports = CbaThanksNotification.objects.filter(facility=location,
                                                       contact=worker,
                                                       date__year=last_year,
                                                       date__month=last_month)
        if reports:
            continue
        name = worker.name
        month = month_ago.strftime("%B")

        births = PatientEvent.objects.filter(event__name__iexact='birth',
                                             cba_conn__contact=worker,
                                             date_logged__year=last_year,
                                             date_logged__month=last_month).distinct().count()

        tolds = PatientTrace.objects.exclude\
        (initiator_contact=None).filter(
                                        messenger=worker,
                                        reminded_date__year=last_year,
                                        reminded_date__month=last_month
                                        ).distinct().count()

        confirms = PatientTrace.objects.exclude\
        (initiator_contact=None).filter(
                                        messenger=worker,
                                        confirmed_date__year=last_year,
                                        confirmed_date__month=last_month
                                        ).distinct().count()

        helps = births + tolds + confirms
        if helps == 0:
            continue

        msg = (CBA_THANKS_MSG % {'name':name, 'month':month,
               'year':last_year, 'helps':helps})

        CbaThanksNotification.objects.create(contact=worker,
                                             facility=location, type='M',
                                             births=births,
                                             date=month_ago)

        OutgoingMessage(worker.default_connection, msg).send()
        counter = counter + 1
        if counter >= msg_limit:
            break

def send_cba_encouragement(router):
    logger.info('encouraging CBAs to continue doing BIRTH, TRACE & TOLD')
    workers = Contact.active.filter(types=get_cba_type())
    if not workers:
        logger.warning('No CBAs found in the system')
        return
    today = date.today()
    todaysday = today.day

    if todaysday <= 14 and settings.ON_LIVE_SERVER:
        return

    counter = 0
    msg_limit = 9
    for worker in workers:
        location = get_clinic_or_default(worker)
        sent = CbaEncouragement.objects.filter(facility=location,
                                               contact=worker,
                                               date_sent__year=today.year,
                                               date_sent__month=today.month)
        if sent:
            continue
        name = worker.name

        msg = (CBA_REMINDER_MSG % {'name': name})

        CbaEncouragement.objects.create(contact=worker, facility=location,
                                        type='M')

        OutgoingMessage(worker.default_connection, msg).send()
        counter = counter + 1
        if counter >= msg_limit:
            break
