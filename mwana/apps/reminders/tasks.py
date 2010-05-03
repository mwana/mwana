import datetime
import logging

from django.utils.translation import ugettext as _

from rapidsms.models import Connection
from rapidsms.messages.outgoing import OutgoingMessage

from mwana.apps.reminders import models as reminders
from mwana import const


NOTIFICATION_NUM_DAYS = 2 # send reminders 2 days before scheduled appointments

logger = logging.getLogger('mwana.apps.reminders.tasks')


def send_appointment_reminder(patient, default_conn=None, pronouns=None):
    if pronouns is None:
        pronouns = {}
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
        if connection.contact:
            cba_name = ' %s' % connection.contact.name
        else:
            cba_name = ''
        if patient.location:
            if patient.location.type == const.get_zone_type() and\
               patient.location.parent:
                clinic_name = patient.location.parent.name
            else:
                clinic_name = patient.location.name
        else:
            clinic_name = 'the clinic'
        msg = OutgoingMessage(connection, _("Hello%(cba)s. %(patient)s is due "
                              "for %(gender)s next clinic appointment. Please "
                              "deliver a reminder to this person and ensure "
                              "%(pronoun)s visits %(clinic)s within 3 days."),
                              cba=cba_name, patient=patient.name,
                              gender=pronouns.get('possessive', 'his or her'),
                              pronoun=pronouns.get('standard', 'he or she'),
                              clinic=clinic_name)
        msg.send()
    return connections


def send_notifications(router):
    logger.info('Sending notifications')
    for appointment in reminders.Appointment.objects.all():
        total_days = appointment.num_days - NOTIFICATION_NUM_DAYS
        date = datetime.datetime.now() -\
               datetime.timedelta(days=total_days)
               
        patient_events = reminders.PatientEvent.objects.filter(
            event=appointment.event,
            date__lte=date,
            patient__is_active=True
        ).exclude(
            sent_notifications__appointment=appointment
        )
        for patient_event in patient_events:
            pronouns = {
                'possessive': patient_event.event.possessive_pronoun,
                'standard': patient_event.event.pronoun,
            }
            connections = send_appointment_reminder(patient_event.patient,
                                                    patient_event.cba_conn,
                                                    pronouns)
            for connection in connections:
                reminders.SentNotification.objects.create(
                                           appointment=appointment,
                                           patient_event=patient_event,
                                           recipient=connection,
                                           date_logged=datetime.datetime.now())
