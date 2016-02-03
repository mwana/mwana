# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.act.messages import CLIENT_LAB_MESSAGE
from mwana.apps.act.messages import CLIENT_PHARMACY_MESSAGE
from mwana.apps.act.messages import CHW_MESSAGE

import datetime
import logging

from rapidsms.models import Connection
from rapidsms.messages.outgoing import OutgoingMessage

from mwana.apps.act import models as act


_ = lambda s: s

NOTIFICATION_NUM_DAYS = 2 # send reminders 2 days before scheduled appointments

logger = logging.getLogger('mwana.apps.experimental.extended_reminders.tasks')


# def send_extended_appointment_reminder(patient_event, appointment, default_conn=None,
#                                        pronouns=None):
#     if pronouns is None:
#         pronouns = {}
#     patient = patient_event.patient
#     type = appointment.name
#     logger.info('Sending appointment reminder for %s' % patient)
#     if patient.location:
#         logger.debug('using patient location (%s) to find CBAs' %
#                      patient.location)
#         # if the cba was registered, we'll have a location on
#         # the patient and can use that information to find the CBAs to whom
#         # we should send the appointment reminders
#         # TODO: also check child locations?
#         connections = list(Connection.objects.filter(
#             contact__types__slug=const.CBA_SLUG,
#             contact__location=patient.location,
#             contact__is_active=True))
#         logger.debug('found %d CBAs to deliver reminders to' %
#                      len(connections))
#     elif default_conn:
#         logger.debug('no patient location; using default_conn')
#         # if the CBA was not registered, just send the notification to the
#         # CBA who logged the event
#         connections = [default_conn]
#     else:
#         logger.debug('no patient location or default_conn; not sending any '
#                      'reminders')
#
#     for connection in connections:
#         lang_code = None
#         if connection.contact:
#             lang_code = connection.contact.language
#             cba_name = ' %s' % connection.contact.name
#         else:
#             cba_name = ''
#         if patient.location:
#             if patient.location.type.slug in const.ZONE_SLUGS and \
#                     patient.location.parent:
#                 clinic_name = patient.location.parent.name
#             else:
#                 clinic_name = patient.location.name
#         else:
#             clinic_name = 'the clinic'
#         appt_date = patient_event.date + \
#                     datetime.timedelta(days=appointment.num_days)
#         msg = OutgoingMessage(connection, EVENT_DUE_NOTIFICATION_MSG,
#                               cba=cba_name, patient=patient.name,
#                               date=appt_date.strftime('%d/%m/%Y'),
#                               clinic=clinic_name, type=translator.translate(lang_code, type))
#
#         msg.send()
#
#         reminders.SentNotification.objects.create(
#             appointment=appointment,
#             patient_event=patient_event,
#             recipient=connection,
#             date_logged=datetime.datetime.now())
#
#     patient_trace = PatientTrace()
#     patient_trace.type = appointment.name
#     patient_trace.start_date = datetime.datetime.now()
#     patient_trace.name = patient_event.patient.name[:50]
#     patient_trace.patient_event = patient_event
#     patient_trace.status = 'new'
#     patient_trace.clinic = get_clinic_or_default(patient_event.patient)
#     patient_trace.initiator = patienttracing.get_initiator_automated()
#     patient_trace.save()


def send_notifications(router):
    logger.info('Sending act notifications')
    if not act.RemindersSwitch.objects.filter(can_send_reminders=True).exists():
        logger.warn('Sending act notifications is not enabled Reminders Switch')
        return

    today = datetime.date.today()
    appointments = act.Appointment.objects.filter(status='pending', date__gte=today)

    for reminder_type in act.ReminderDay.objects.all():
        appointment_date = today + datetime.timedelta(days=reminder_type.days)
        few_days_before_apnt_date = appointment_date - datetime.timedelta(days=3)
        # @type reminder_type ReminderDay
        for appointment in appointments.filter(type=reminder_type.appointment_type).filter(
                date__gte=few_days_before_apnt_date).filter(date__lte=appointment_date):
            if act.SentReminder.objects.filter(appointment=appointment, reminder_type=reminder_type).exists():
                continue

            client = appointment.client
            chw = appointment.cha_responsible
            print "Is client eligible", client.is_eligible_for_messaging()
            if client.is_eligible_for_messaging():
                conn = client.connection
                if conn:
                    template = CLIENT_LAB_MESSAGE if appointment.type == appointment.get_lab_type() else CLIENT_PHARMACY_MESSAGE
                    OutgoingMessage(connection=conn, template=template,
                                    date=appointment.date.strftime('%d/%m/%Y')).send()
                    act.SentReminder.objects.get_or_create(appointment=appointment, reminder_type=reminder_type, phone=client.phone)
                else:
                    logging.error(
                        "Failed to send message to client %s with phone %s. No matching connection object found" % (
                            client.alias, client.phone))

            if chw and chw.phone_verified:
                chw_conn = chw.connection
                if chw_conn:
                    OutgoingMessage(connection=conn, template=CHW_MESSAGE, name=chw.name, client=client.alias,
                                    visit_type=appointment.get_type_display(),
                                    date=appointment.date.strftime('%d/%m/%Y')).send()
                    act.SentReminder.objects.get_or_create(appointment=appointment, reminder_type=reminder_type, phone=chw.phone)
                else:
                    logging.error(
                        "Failed to send message to CHW %s with phone %s. No matching connection object found" % (
                            chw.__unicode__(), chw.phone))
