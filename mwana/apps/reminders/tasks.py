# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.translator.util import Translator
import datetime
import logging

from rapidsms.models import Connection
from rapidsms.messages.outgoing import OutgoingMessage

from mwana.apps.reminders import models as reminders
from mwana import const
from mwana.apps.patienttracing.models import PatientTrace
from mwana.apps.patienttracing import models as patienttracing

# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that makemessages finds
# our text.
_ = lambda s: s

translator = Translator()

NOTIFICATION_NUM_DAYS = 2 # send reminders 2 days before scheduled appointments

logger = logging.getLogger('mwana.apps.reminders.tasks')


def send_appointment_reminder(patient_event, appointment, default_conn=None,
                              pronouns=None):
    if pronouns is None:
        pronouns = {}
    patient = patient_event.patient
    type = appointment.name
    logger.info('Sending appointment reminder for %s' % patient)
    if patient.location:
        logger.debug('using patient location (%s) to find CBAs' %
                      patient.location)
        # if the cba was registered, we'll have a location on
        # the patient and can use that information to find the CBAs to whom
        # we should send the appointment reminders
        # TODO: also check child locations?
        connections = list(Connection.objects.filter(
                                         contact__types__slug=const.CBA_SLUG,
                                         contact__location=patient.location,
                                         contact__is_active=True))
        logger.debug('found %d CBAs to deliver reminders to' %
                      len(connections))
    elif default_conn:
        logger.debug('no patient location; using default_conn')
        # if the CBA was not registered, just send the notification to the
        # CBA who logged the event
        connections = [default_conn]
    else:
        logger.debug('no patient location or default_conn; not sending any '
                      'reminders')

    for connection in connections:
        lang_code = None
        if connection.contact:
            lang_code = connection.contact.language
            cba_name = ' %s' % connection.contact.name
        else:
            cba_name = ''
        if patient.location:
            if patient.location.type.slug in const.ZONE_SLUGS and\
               patient.location.parent:
                clinic_name = patient.location.parent.name
            else:
                clinic_name = patient.location.name
        else:
            clinic_name = 'the clinic'
        appt_date = patient_event.date +\
                    datetime.timedelta(days=appointment.num_days)
        msg = OutgoingMessage(connection, _("Hi%(cba)s.%(patient)s is due for "
                              "%(type)s clinic visit on %(date)s.Please "
                              "remind them to visit %(clinic)s, then "
                              "reply with TOLD %(patient)s"),
                              cba=cba_name, patient=patient.name,
                              date=appt_date.strftime('%d/%m/%Y'),
                              clinic=clinic_name, type=translator.translate(lang_code, type))
        
        msg.send()
        
        reminders.SentNotification.objects.create(
                                   appointment=appointment,
                                   patient_event=patient_event,
                                   recipient=connection,
                                   date_logged=datetime.datetime.now())

    patient_trace = PatientTrace()
    patient_trace.type = appointment.name
    patient_trace.start_date=datetime.datetime.now()
    patient_trace.name = patient_event.patient.name[:50]
    patient_trace.patient_event = patient_event
    patient_trace.status = 'new'
    patient_trace.initiator = patienttracing.get_initiator_automated()
    patient_trace.save()


def send_notifications(router):
    logger.info('Sending notifications')
    for appointment in reminders.Appointment.objects.all():
        # the number of days after a patient event that we want to send a
        # reminder for this appointment
        total_days = appointment.num_days - NOTIFICATION_NUM_DAYS
        # the date before which a patient event must have occurred in order
        # to trigger a reminder
        date = datetime.datetime.now() -\
               datetime.timedelta(days=total_days)
        # the beginning of that day
        start_date = date.replace(minute=0, second=0, hour=0)
        # the end of that day
        end_date = start_date + datetime.timedelta(days=1)
        # only send appointment reminders that are due TODAY to avoid spamming
        # the CBAs / HSAs with excessive, out-dated reminders
        patient_events = reminders.PatientEvent.objects.filter(
            event=appointment.event,
            date__gte=start_date,
            date__lt=end_date,
            patient__is_active=True
        ).exclude(
            sent_notifications__appointment=appointment
        )
        for patient_event in patient_events:
            connections = send_appointment_reminder(patient_event,
                                                    appointment,
                                                    patient_event.cba_conn)
