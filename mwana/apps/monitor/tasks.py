# vim: ai ts=4 sts=4 et sw=4
from datetime import date
import logging

from django.db.models import Count
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact
from mwana.apps.training.models import TrainingSession, Trained
from mwana.apps.reports.models import SupportedLocation
from mwana.apps.reports.webreports.models import GroupFacilityMapping
from mwana.apps.reports.webreports.models import ReportingGroup
from datetime import date
from rapidsms.models import Contact
from mwana.apps.locations.models import Location
from mwana.apps.reminders.models import PatientEvent
from mwana.apps.labresults.models import SampleNotification
from mwana.apps.hub_workflow.models import HubSampleNotification

logger = logging.getLogger(__name__)

today = date.today()

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

def update_supported_sites():
    logger.info("In update_supported_sites")
#    TODO uses methods from mwana.const instead of string constants for worker
#    types

#    update based on reported training sessions
    t_sessions=TrainingSession.objects.exclude(location__name__icontains='Train', location__slug__endswith='00').exclude(location__name__icontains='Support')
    for ts in t_sessions:
        loc=ts.location;loc.send_live_results=True;loc.save(); a,b=SupportedLocation.objects.get_or_create(location=loc)

#    update based on active registered staff, printers
    for contact in Contact.active.filter(types__slug='worker'):
        a,b=SupportedLocation.objects.get_or_create(location=contact.location)
        
#update site with dbs printer
    for contact in Contact.active.filter(types__slug='dbs-printer'):
        loc=contact.location
        loc.has_independent_printer=True;loc.save()

#    update based on trained user's reports
    trained=Trained.objects.exclude(location__name__icontains='Train').exclude(location__slug__endswith='00').exclude(location__name__icontains='Support')#.exclude(location__type__slug='zone');

    for ts in trained:
        loc=ts.location;
        if ts.location.type.slug == 'zone':
            loc=ts.location.parent
            loc.send_live_results=True
            loc.save()
            a,b=SupportedLocation.objects.get_or_create(location=loc)

        if ts.trained_by:
            a,b=GroupFacilityMapping.objects.get_or_create(group=ts.trained_by, facility=loc)

def inactivate_sms_users_without_connections():
    logger.info("inactivate_sms_users_without_connections")
    slugs = ['worker', 'hub', 'district', 'province', 'dbs-printer']
    for cont in Contact.active.filter(connection=None, types__slug__in=slugs):
        cont.is_active=False
        cont.save()


def delete_spurious_supported_sites():
    logger.info("delete_spurious_supported_sites")
    SupportedLocation.objects.filter(location__slug__endswith='00').delete()
    SupportedLocation.objects.filter(location__parent=None).delete()
    SupportedLocation.objects.filter(location__parent__parent=None).delete()
    SupportedLocation.objects.filter(location__type__slug='zone').delete()
    SupportedLocation.objects.filter(location__name__istartswith='Training').delete()
    SupportedLocation.objects.filter(location__name__istartswith='Support').delete()


def delete_spurious_group_facility_mappings():
    logger.info("In delete_spurious_group_facility_mappings")
    GroupFacilityMapping.objects.filter(facility__slug__endswith='00').delete()
    GroupFacilityMapping.objects.filter(facility__type__slug='zone').delete()
    GroupFacilityMapping.objects.filter(facility__slug__endswith='00').delete()
    GroupFacilityMapping.objects.filter(facility__name__istartswith='Training').delete()
    GroupFacilityMapping.objects.filter(facility__name__istartswith='Support').delete()

#synchronize
def try_assign(group, facilities):
    for loc in facilities:
        GroupFacilityMapping.objects.get_or_create(group=group, facility=loc)

def update_overall_groups():
    logger.info("updating overall groups - Support, MoH HQ, CDC")
    group = ReportingGroup.objects.get(name__icontains='Support')

    for sl in SupportedLocation.objects.all():
        a,b=GroupFacilityMapping.objects.get_or_create(group=group, facility=sl.location)

    facilities = Location.objects.exclude(groupfacilitymapping__group=None)

    reporting_group = None
    groups = ["support", "moh", "cdc"]

    for group in groups:
        try:
            reporting_group = ReportingGroup.objects.get(name__icontains=group)
        except:
            logger.error("Reporting group matching '%s' not found" % group)

        if reporting_group and facilities:
            try_assign(reporting_group, facilities)
        
def delete_training_births():
    logger.info("deleting training births")
    # clear loveness bwalya patient events
    PatientEvent.objects.filter(patient__name__istartswith='lo').filter(patient__name__icontains='nes').filter(patient__name__icontains='bwal').delete()

    PatientEvent.objects.filter(patient__location__name__istartswith='Training').delete()

def close_open_old_training_sessions():
    logger.info("Closing obsolete training sessions")
    for ts in TrainingSession.objects.filter(is_on=True).exclude(start_date__gte=today):
        ts.is_on=False
        ts.save()

def delete_training_sample_notifications():
    logger.info("deleting training sample notifications")
    SampleNotification.objects.filter(count__gte=80).delete()
    HubSampleNotification.objects.filter(count__gte=120).delete()

def clear_en_language_code():
    logger.info("In clear_en_language_code")
    for cont in Contact.objects.filter(language='en'):
        cont.language=''
        cont.save()

def update_sub_groups():
    logger.info("updating sub groups - PHOs, DHOs, UNICEF, IDInsight")
    for sl in SupportedLocation.objects.all():
        loc=sl.location;loc.send_live_results=True;
        loc.save();
        dho="DHO %s" % loc.parent.name;
        pho="PHO %s" % loc.parent.parent.name
        try:
            group=ReportingGroup.objects.get(name=dho)
            try_assign(group,[loc])
            group=ReportingGroup.objects.get(name=pho)
            try_assign(group,[loc])

            if loc.parent.slug in ['106000','302000', '301000', '901000', '903000']:
                idinsight = ReportingGroup.objects.get(name__iexact='idinsight')
                try_assign(idinsight,[loc])
                unicef = ReportingGroup.objects.get(name__iexact='unicef')
                try_assign(unicef,[loc]);
        except Exception, e:
            logger.error("%s. Location: %s" % (e, loc))

def cleanup_data(router):
    logger.info('cleaning up data, updating supported sites')
    
    update_supported_sites()
    close_open_old_training_sessions()
    delete_training_births()
    delete_training_sample_notifications()
    inactivate_sms_users_without_connections()
    clear_en_language_code()

    update_overall_groups()

    delete_spurious_group_facility_mappings()
    delete_spurious_supported_sites()
    update_sub_groups()
    
