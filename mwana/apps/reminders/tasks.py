import datetime

from rapidsms.models import Connection
from rapidsms.messages.outgoing import OutgoingMessage

from mwana.apps.reminders import models as reminders

NOTIFICATION_NUM_DAYS = 2 # send reminders 2 days before scheduled appointments


def send_notification(patient_event, appointment):
    patient = patient_event.patient
    if patient.location and patient.zone_code is not None:
        # if the cba was registered, we'll have a location and zone_code on
        # the patient and can use that information to find the CBAs to whom
        # we should send the appointment reminders
        connections = Connection.objects.filter(contact__types__slug='cba',
                                         contact__location=patient.location,
                                         contact__zone_code=patient.zone_code)
    else:
        # if the CBA was not registered, just send the notification to the
        # CBA who logged the event
        connections = [patient_event.cba_conn]
    
    for connection in connections:
        if connection.contact:
            cba_name = ' %s' % connection.contact.name
        else:
            cba_name = ''
        if patient_event.patient.location:
            clinic_name = patient_event.patient.location
        else:
            clinic_name = 'the clinic'
        msg = OutgoingMessage(connection, "Hello%(cba)s. %(patient)s is due "
                              "for %(gender)s next clinic appointment. Please "
                              "deliver a reminder to this person and ensure "
                              "%(pronoun)s visits %(clinic)s within 3 days.",
                              cba=cba_name, patient=patient_event.patient.name,
                              gender=patient_event.event.possessive_pronoun,
                              pronoun=patient_event.event.pronoun,
                              clinic=clinic_name)
        msg.send()
        reminders.SentNotification.objects.create(appointment=appointment,
                                           patient_event=patient_event,
                                           recipient=connection,
                                           date_logged=datetime.datetime.now())


def send_notifications(router):
    for appointment in reminders.Appointment.objects.all():
        total_days = appointment.num_days - NOTIFICATION_NUM_DAYS
        date = datetime.datetime.now() -\
               datetime.timedelta(days=total_days)
               
        patient_events = reminders.PatientEvent.objects.filter(
            event=appointment.event,
            date__lte=date,
        ).exclude(
            sent_notifications__appointment=appointment
        )
        for patient_event in patient_events:
            send_notification(patient_event, appointment)
