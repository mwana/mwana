# vim: ai ts=4 sts=4 et sw=4
#TODO write unit tests for this module
from mwana.apps.monitor.models import UnrecognisedResult
from mwana.apps.reports.models import Turnaround
from mwana.apps.userverification.models import DeactivatedUser
from datetime import date
from datetime import datetime
from datetime import timedelta
import logging

from django.db.models import Count
from mwana.apps.alerts.models import Lab
from mwana.apps.email.sender import EmailSender
from mwana.apps.hub_workflow.models import HubSampleNotification
from mwana.apps.issuetracking.utils import get_admin_email_address
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.models import SampleNotification
from mwana.apps.locations.models import Location
from mwana.apps.monitor.data_integrity import dbs_with_date_issues
from mwana.apps.monitor.models import LostContactsNotification
from mwana.apps.monitor.models import Support
from mwana.apps.patienttracing.management.commands.correct_automated_traces import correct_patient_traces
from mwana.apps.reminders.models import PatientEvent
from mwana.apps.reports.models import SupportedLocation
from mwana.apps.reports.webreports.models import GroupFacilityMapping
from mwana.apps.reports.webreports.models import ReportingGroup
from mwana.apps.training.models import Trained
from mwana.apps.training.models import TrainingSession
from mwana.const import get_dbs_printer_type
from mwana.const import get_lab_worker_type
from mwana.util import is_today_a_weekend
from rapidsms.contrib.messagelog.models import Message
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
    results = Result.objects.filter(arrival_date__year=year(),
                                    arrival_date__month=month(),
                                    arrival_date__day=day())
    p = Payload.objects.filter(incoming_date__year=year(),
                               incoming_date__month=month(),
                               incoming_date__day=day()). \
        values("source").annotate(Count('id'))
    return "\n".join(entry['source'].split('/')[1].title().replace(
                     'Arthur-Davison', 'ADH').replace('Kalingalinga', 'Kalis')
                     + ":" + str(entry['id__count']) + "/" +
                     str(results.filter(payload__source__icontains=entry['source']).count()) for entry in p)


def get_results_data():
    sent_today = Result.objects.filter(notification_status='sent',
                                       result_sent_date__year=year(),
                                       result_sent_date__month=month(),
                                       result_sent_date__day=day()
                                       ).count()
    new = Result.objects.filter(notification_status='new').count()
    notified = Result.objects.filter(notification_status='notified').count()

    return "New:%s\nNotified:%s\nSent:%s" % (new, notified, sent_today)


def get_messages_data():
    msgs_i = Message.objects.exclude(connection__backend__name='message_tester'). \
        filter(date__year=year(), date__month=month(),
               date__day=day(), direction='I'). \
        values('connection__backend__name'). \
        annotate(Count('id'))

    msgs_o = Message.objects.exclude(connection__backend__name='message_tester'). \
        filter(date__year=year(), date__month=month(),
               date__day=day(), direction='O'). \
        values('connection__backend__name'). \
        annotate(Count('id'))

    my_map = {}
    for entry in msgs_i:
        my_map[entry['connection__backend__name']] = "%s" % entry['id__count']

    for entry in msgs_o:
        k = entry['connection__backend__name']
        v = entry['id__count']
        if k in my_map:
            my_map[k] = my_map[k] + "/%s" % v
        else:
            my_map[k] = "0/%s" % v

    return "\n".join("%s:%s" % (k, v) for k, v in my_map.items())


def send_report_to_lab_workers():
    logger.info('sending monitoring information to support staff at lab')
    if is_today_a_weekend():
        return

    today = datetime.today()
    my_date = datetime(today.year, today.month, today.day)

    if today.hour < 12:
        return

    lab_workers = Contact.active.filter(types=get_lab_worker_type()). \
        exclude(connection=None)

    for lab_worker in lab_workers:
        lab = Lab.objects.filter(phone__endswith=lab_worker.default_connection.identity[-10:])
        if not lab:
            continue

        my_lab = lab[0]
        res = Result.objects.filter(sample_id__startswith=my_lab.lab_code,
                                    payload__incoming_date__year=my_date.year,
                                    payload__incoming_date__month=my_date.month,
                                    payload__incoming_date__day=my_date.day
                                    ).count()

        message = ("Hi %(name)s. Today Mwana server has received"
                   " %(res)s results from %(lab)s" % {
                   "name": lab_worker.name, "lab": my_lab.source_key.title(), "res": res})

        OutgoingMessage(lab_worker.default_connection, message).send()


def send_monitor_report(router):
    logger.info('sending monitoring information to support staff')

    admins = Contact.active.filter(is_help_admin=True,
                                   monitormessagerecipient__receive_sms=True)

    if not admins:
        logger.warning('No admins to send monitoring data to were found in system')
        return
    message = "Sys. Info\n_Payloads/Res_\n%s\n_Results_\n%s\n_SMS_(I/O)\n%s" % (
                                                                                get_payload_data(), get_results_data(), get_messages_data())
    logger.info('Sending msg: %s' % message)

    for admin in admins:
        OutgoingMessage(admin.default_connection, message).send()

    send_report_to_lab_workers()


def update_supported_sites():
    logger.info("In update_supported_sites")
    #    TODO uses methods from mwana.const instead of string constants for worker
    #    types

    #    update based on reported training sessions
    t_sessions = TrainingSession.objects.exclude(location__name__icontains='Train',
                                                 location__slug__endswith='00').\
        exclude(location__name__icontains='Support')
    for ts in t_sessions:
        loc = ts.location
        loc.send_live_results = True
        loc.save()
        a, b = SupportedLocation.objects.get_or_create(location=loc)

    #    update based on active registered staff, printers
    for contact in Contact.active.filter(types__slug='worker'):
        loc = contact.location
        loc.send_live_results = True
        a, b = SupportedLocation.objects.get_or_create(location=contact.location)

    #update site with dbs printer
    for contact in Contact.active.filter(types__slug='dbs-printer'):
        loc = contact.location
        loc.send_live_results = True
        loc.has_independent_printer = True;
        loc.save()
        a, b = SupportedLocation.objects.get_or_create(location=contact.location)

    #    update based on trained user's reports
    trained = Trained.objects.exclude(location__name__icontains='Train').exclude(location__slug__endswith='00').exclude(
                                                                                                                        location__name__icontains='Support')#.exclude(location__type__slug='zone');

    for ts in trained:
        loc = ts.location;
        if ts.location.type.slug == 'zone':
            loc = ts.location.parent
            loc.send_live_results = True
            loc.save()
            a, b = SupportedLocation.objects.get_or_create(location=loc)

        if ts.trained_by:
            a, b = GroupFacilityMapping.objects.get_or_create(group=ts.trained_by, facility=loc)

        #    update based on results retrieved
    results = Result.objects.filter(result_sent_date__year=datetime.today().year
                                    , clinic__supportedlocation=None)

    for res in results:
        # @type res Result
        loc = res.clinic;
        a, b = SupportedLocation.objects.get_or_create(location=loc)


def inactivate_sms_users_without_connections():
    logger.info("inactivate_sms_users_without_connections")
    slugs = ['worker', 'hub', 'district', 'province', 'dbs-printer', 'cba']
    for cont in Contact.active.filter(connection=None, types__slug__in=slugs):
        cont.is_active = False
        cont.save()


def date_of_most_recent_incoming_msg(contact):
    msgs = Message.objects.filter(contact=contact, direction='I').order_by('-date')
    if msgs:
        return msgs[0].date
    else:
        return None


def date_of_most_recent_outgoing_msg(contact):
    msgs = Message.objects.filter(contact=contact, direction='O').order_by('-date')
    if msgs:
        return msgs[0].date
    else:
        return None


def inactivate_unresponsive_dbs_printers():
    logger.info("inactivate_unresponsive_dbs_printers")

    active_printers = Contact.active.filter(types=get_dbs_printer_type())

    for printer in active_printers:
        last_incoming_smg_date = date_of_most_recent_incoming_msg(printer)
        last_outgoing_smg_date = date_of_most_recent_outgoing_msg(printer)
        if last_incoming_smg_date and last_outgoing_smg_date:
            diff = (last_outgoing_smg_date - last_incoming_smg_date).days
            if diff > 7:
                now = datetime.today()
                today = datetime(now.year, now.month, now.day)
                days_ago = today - timedelta(days=3)
                # check if printer was sent a message just before today
                if Message.objects.filter(contact=printer, date__gte=days_ago, date__lt=today):
                    # @type printer Contact
                    printer.is_active = False
                    printer.save()
                    logger.warn(
                                "%s with connection %s has been inactivated for being unresponsive for possibly %s days" % (
                                printer, printer.default_connection, diff))

        elif last_outgoing_smg_date and not last_incoming_smg_date:
            if Message.objects.filter(contact=printer).count() > 10:# 10 is arbitrary
                printer.is_active = False
                printer.save()
                logger.warn("%s with connection %s has been inactivated for being unresponsive" % (
                            printer, printer.default_connection))


def delete_spurious_supported_sites():
    logger.info("delete_spurious_supported_sites")
    SupportedLocation.objects.filter(location__slug__endswith='00').delete()
    SupportedLocation.objects.filter(location__parent=None).delete()
    SupportedLocation.objects.filter(location__parent__parent=None).delete()
    SupportedLocation.objects.filter(location__type__slug='zone').delete()
    SupportedLocation.objects.filter(location__name__istartswith='Training').delete()
    SupportedLocation.objects.filter(location__name__istartswith='Support').delete()

    for loc in Location.objects.filter(send_live_results=True,
                                       type__slug__in=['province', 'district', 'zone']):
        loc.send_live_results = False
        loc.save()


def delete_spurious_group_facility_mappings():
    logger.info("In delete_spurious_group_facility_mappings")
    GroupFacilityMapping.objects.filter(facility__slug__endswith='00').delete()
    GroupFacilityMapping.objects.filter(facility__type__slug='zone').delete()
    GroupFacilityMapping.objects.filter(facility__slug__endswith='00').delete()
    GroupFacilityMapping.objects.filter(facility__name__istartswith='Training').delete()
    GroupFacilityMapping.objects.filter(facility__name__istartswith='Support').delete()

def try_assign(group, facilities):
    for loc in facilities:
        GroupFacilityMapping.objects.get_or_create(group=group, facility=loc)


def update_overall_groups():
    logger.info("updating overall groups - Support, MoH HQ, CDC")
    group = ReportingGroup.objects.get(name__icontains='Support')

    for sl in SupportedLocation.objects.all():
        a, b = GroupFacilityMapping.objects.get_or_create(group=group, facility=sl.location)

    facilities = Location.objects.exclude(groupfacilitymapping__group=None)

    reporting_group = None
    groups = ["support", "moh", "cdc"]

    for group in groups:
        try:
            reporting_group = ReportingGroup.objects.get(name__icontains=group)
        except ReportingGroup.DoesNotExist:
            logger.error("Reporting group matching '%s' not found" % group)
        except ReportingGroup.MultipleObjectsReturned:
            logger.error("More than one group matching '%s' not found" % group)

        if reporting_group and facilities:
            try_assign(reporting_group, facilities)


def delete_training_births():
    logger.info("deleting training births")
    # clear loveness bwalya patient events
    PatientEvent.objects.filter(patient__name__icontains='loveness bwalya').delete()
    Contact.objects.filter(name__icontains='loveness bwalya').delete()
    PatientEvent.objects.filter(patient__name__istartswith='lo').filter(patient__name__icontains='nes').filter(
                                                                                                               patient__name__icontains='bwal').delete()
    Contact.objects.filter(name__istartswith='lo').filter(name__icontains='nes') \
        .filter(name__icontains='bwal').delete()

    PatientEvent.objects.filter(patient__location__name__istartswith='Training').delete()
    from datetime import datetime

    if datetime.now().hour > 18:
        for c in Contact.objects.filter(location__name__icontains='Training', is_active=True):
            c.is_active = False
            c.save()
        for c in Contact.objects.filter(location__parent__name__icontains='Training', is_active=True):
            c.is_active = False
            c.save()


def close_open_old_training_sessions():
    logger.info("Closing obsolete training sessions")
    for ts in TrainingSession.objects.filter(is_on=True).exclude(start_date__gte=date.today()):
        ts.is_on = False
        ts.save()


def delete_training_sample_notifications():
    logger.info("deleting training sample notifications")
    SampleNotification.objects.filter(count__gte=80).delete()
    HubSampleNotification.objects.filter(count__gte=120).delete()
    for ts in TrainingSession.objects.all():
        d = ts.start_date
        a = datetime(d.year, d.month, d.day)
        b = a + timedelta(days=1)
        SampleNotification.objects.filter(location=ts.location, date__gt=a, date__lt=b).delete()
        HubSampleNotification.objects.filter(clinic=ts.location, date__gt=a, date__lt=b).delete()


def clear_en_language_code():
    logger.info("In clear_en_language_code")
    for cont in Contact.objects.filter(language='en'):
        cont.language = ''
        cont.save()


def update_sub_groups():
    logger.info("updating sub groups - PHOs, DHOs, UNICEF")
    for sl in SupportedLocation.objects.all():
        loc = sl.location;
        loc.send_live_results = True;
        loc.save();
        dho = "DHO %s" % loc.parent.name;
        pho = "PHO %s" % loc.parent.parent.name
        try:
            group = ReportingGroup.objects.get(name=dho)
            try_assign(group, [loc])
            group = ReportingGroup.objects.get(name=pho)
            try_assign(group, [loc])


            unicef = ReportingGroup.objects.get(name__iexact='unicef')
            mgic = ReportingGroup.objects.get(name__iexact='MGIC Zambia')

            if loc.parent.slug in ['106000', '302000', '301000', '901000', '903000']:
                try_assign(unicef, [loc]);
            if loc.parent.parent.slug == '800000':
                try_assign(mgic, [loc]);
        except ReportingGroup.DoesNotExist, e:
            ReportingGroup.objects.get_or_create(name=dho)
            ReportingGroup.objects.get_or_create(name=pho)
            logger.error("%s. Location: %s. Dho: %s. Pho: %s" % (e, loc, dho, pho))


def mark_long_pending_results_as_obsolete():
    """
    When results stay unretrieved for too long from the time they were ready,
    mark them as obsolete
    """

    logger.info('in mark_long_pending_results_as_obsolete')
    now = datetime.today()

    #approximate
    last_month = now - timedelta(days=31)
    two_months_ago = date.today() - timedelta(days=60)

    # based on arrival_date
    for res in Result.objects.filter(notification_status__in=['new', 'notified'],
                                     arrival_date__lt=last_month).\
                                     exclude(verified=False):
        # @type res Result
        res.notification_status = 'obsolete'
        res.save()
    # based on processed_on
    for res in Result.objects.filter(notification_status__in=['new', 'notified'],
                                     processed_on__lt=two_months_ago).\
                                     exclude(verified=False):
        # @type res Result
        res.notification_status = 'obsolete'
        res.save()


def mark_sent_results_with_date_inconsitencies_as_obsolete():
    """
    When results have already been sent to facilities but have data integity
    issues with dates mark them as obsolete. (see data_integrity.py)
    """

    logger.info('in mark_sent_results_with_date_inconsitencies_as_obsolete')
    counter = 0
    for res in dbs_with_date_issues().filter(notification_status='sent'):
        # @type res Result
        res.notification_status = 'obsolete'
        res.save()
        counter += 1

    # Arbitrary too high figure for transport time is used
    bad_turnaround = Turnaround.objects.filter(transporting__gt=300)
    for res in Result.objects.filter(id__in=bad_turnaround, notification_status='sent'):
        # @type res Result
        res.notification_status = 'obsolete'
        res.save()
        counter += 1

    logger.info('%s dbs marked as obsolete' % counter)


def try_correct_unrecognised_results():
    for record in UnrecognisedResult.objects.all():
        for res in Result.objects.filter(clinic=None, clinic_code_unrec=record.clinic_code_unrec):
            res.clinic = record.intended_clinic
            res.save()


def cleanup_data(router):
    logger.info('cleaning up data, updating supported sites')
    try_correct_unrecognised_results()

    try:
        mark_sent_results_with_date_inconsitencies_as_obsolete()
    except Exception, e:
        logger.error('mark_sent_results_with_date_inconsitencies_as_obsolete(). %s', e)

    try:
        update_supported_sites()
    except Exception, e:
        logger.error('update_supported_sites(). %s', e)

    try:
        close_open_old_training_sessions()
    except Exception, e:
        logger.error('close_open_old_training_sessions(). %s', e)

    try:
        delete_training_births()
    except Exception, e:
        logger.error('delete_training_births(). %s', e)

    try:
        delete_training_sample_notifications()
    except Exception, e:
        logger.error('delete_training_sample_notifications(). %s', e)

    try:
        inactivate_sms_users_without_connections()
    except Exception, e:
        logger.error('inactivate_sms_users_without_connections(). %s', e)

    try:
        inactivate_unresponsive_dbs_printers()
    except Exception, e:
        logger.error('inactivate_unresponsive_dbs_printers(). %s', e)

    try:
        clear_en_language_code()
    except Exception, e:
        logger.error('clear_en_language_code(). %s', e)

    try:
        update_overall_groups()
    except Exception, e:
        logger.error('update_overall_groups(). %s', e)

    try:
        delete_spurious_group_facility_mappings()
    except Exception, e:
        logger.error('delete_spurious_group_facility_mappings(). %s', e)

    try:
        delete_spurious_supported_sites()
    except Exception, e:
        logger.error('delete_spurious_supported_sites(). %s', e)

    try:
        update_sub_groups()
    except Exception, e:
        logger.error('update_sub_groups(). %s', e)

    try:
        mark_long_pending_results_as_obsolete()
    except Exception, e:
        logger.error('mark_long_pending_results_as_obsolete()). %s', e)

    correct_patient_traces()


def send_notifications_for_clinics_with_no_staff(router):
    logger.info("In send_notifications_for_clinics_with_no_staff")
    email_sender = EmailSender()
    host, user = email_sender.connect()
    today = date.today()
    footer = """

Thank you,
%(admin)s

----------------------------------------------
Do not reply. This is a system generated message.
----------------------------------------------
""" % ({'admin': get_admin_email_address()})

    try:
        for support in Support.objects.filter(is_active=True, user__is_active=True,
                                              user__email__icontains='@'):
            exclude = [lcn.facility.id for lcn in LostContactsNotification.\
            objects.filter(sent_to=support, date__gte=(today - timedelta(days=7)))]
            locations = Location.objects.filter(supportedlocation__supported=True,
                                                groupfacilitymapping__group__groupusermapping__user__support=support)\
                .exclude(contact__is_active=True,
                         contact__connection__identity__contains='0').\
                    exclude(id__in=exclude).order_by('parent__parent__name', 'parent__name').distinct()

            if not locations:
                logger.debug("skipping for %s. Locations=%s" % (support.__unicode__(), len(locations)))
                continue

            body = "Dear %s,\n\nThe following facilities have no Results160 Staff.\n" \
                   "The staff indicated have stopped using the Mwana SMS system"\
                   " for unknown reasons\n\n" % support.user.username

            body += "\n".join("- %s, %s, %s, %s. %s" % (
                              loc.parent.parent.name,
                              loc.parent.name, loc.name, loc.slug,
                              ", ".join("%s (%s)" % ( da.contact.name, da.connection.identity)
                                        for da in DeactivatedUser
                                        .objects.filter(contact__location=loc, contact__is_active=False))
                              )
                              for loc in locations)
            body += footer
            logger.info("sending: %s, %s, %s, %s " % (support.user.email, body[:100], host, user))
            email_sender.send([support.user.email], "Facilities with no Results160 Staff", body, host, user)

            for loc in locations:
                LostContactsNotification.objects.create(sent_to=support, facility=loc)
    except Exception, e:
        logger.error('Error when sending notifications_for_clinics_with_no_staff: %s', e)
    finally:
        email_sender.close(host)