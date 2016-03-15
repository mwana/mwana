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

logger = logging.getLogger('mwana.apps.act.tasks')


def send_notifications(router):
    logger.info('Sending act notifications')
    if not act.RemindersSwitch.objects.filter(can_send_reminders=True).exists():
        logger.warn('Sending act notifications is not enabled in Reminders Switch')
        return

    today = datetime.date.today()
    appointments = act.Appointment.objects.filter(status='pending', date__gte=today)

    for reminder_type in act.ReminderDay.objects.filter(activated=True):
        appointment_date = today + datetime.timedelta(days=reminder_type.days)
        few_days_before_apnt_date = appointment_date - datetime.timedelta(days=3)
        # @type reminder_type ReminderDay
        for appointment in appointments.filter(type=reminder_type.appointment_type).filter(
                date__gte=few_days_before_apnt_date).filter(date__lte=appointment_date):

            client = appointment.client
            chw = appointment.cha_responsible

            if client.is_eligible_for_messaging():
                conn = client.connection
                already_sent = act.SentReminder.objects.filter(appointment=appointment, reminder_type=reminder_type,
                                                   phone=client.phone, visit_date=appointment.date).exists()
                if not already_sent:
                    if conn:
                        template = CLIENT_LAB_MESSAGE if appointment.type == appointment.get_lab_type() else CLIENT_PHARMACY_MESSAGE
                        OutgoingMessage(connection=conn, template=template,
                                        date=appointment.date.strftime('%d/%m/%Y')).send()
                        act.SentReminder.objects.get_or_create(appointment=appointment, reminder_type=reminder_type, phone=client.phone, visit_date=appointment.date)
                    else:
                        logging.error(
                            "Failed to send message to client %s with phone %s. No matching connection object found" % (
                                client.alias, client.phone))

            if chw and chw.phone_verified:
                already_sent = act.SentReminder.objects.filter(appointment=appointment, reminder_type=reminder_type,
                                                   phone=chw.phone, visit_date=appointment.date).exists()
                if not already_sent:
                    chw_conn = chw.connection
                    if chw_conn:
                        OutgoingMessage(connection=chw_conn, template=CHW_MESSAGE, name=chw.name, client=client.alias,
                                        visit_type=appointment.get_type_display(),
                                        date=appointment.date.strftime('%d/%m/%Y')).send()
                        act.SentReminder.objects.get_or_create(appointment=appointment, reminder_type=reminder_type,
                                                               phone=chw.phone, visit_date=appointment.date)
                    else:
                        logging.error(
                            "Failed to send message to CHW %s with phone %s. No matching connection object found" % (
                                chw.__unicode__(), chw.phone))
