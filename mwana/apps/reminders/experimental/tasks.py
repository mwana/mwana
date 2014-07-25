# vim: ai ts=4 sts=4 et sw=4
from datetime import date
from datetime import timedelta
import logging

from mwana.apps.locations.models import Location
from mwana.apps.reminders.experimental.models import SentNotificationToClinic
from mwana.apps.reminders.models import Appointment
from mwana.apps.reminders.models import PatientEvent
from mwana.const import get_clinic_worker_type
from rapidsms.messages.outgoing import OutgoingMessage
from mwana.dateutils import week_start
from mwana.dateutils import weekend
from rapidsms.models import Contact

logger = logging.getLogger(__name__)


def _get_num_of_due_appointments(location, appointment, start_date, end_date):
    
    start = start_date - timedelta(days=appointment.num_days)
    end = end_date - timedelta(days=appointment.num_days)
        
    return PatientEvent.objects.filter(event__slug__icontains='birth', patient__is_active=True,
                                       patient__location__parent=location,
                                       date__gte=start).\
        filter(date__lte=end).count()

def send_notifications_to_clinic(router):
    logger.info('Sending event notifications to clinic')
    today = date.today()
    this_week_start = week_start(today)
    this_weekend = weekend(today)

    for location in Location.objects.filter(supported__supported=True):
        if SentNotificationToClinic.objects.filter(location=location,
                                                   date_logged__gte=this_week_start):
            continue

        my_map = {}

        for appointment in Appointment.objects.all():
            my_map[appointment.name] = _get_num_of_due_appointments(location, appointment, this_week_start, this_weekend)

        if not my_map:
            continue

        total = sum(my_map[i] for i in my_map)
        if total == 0:
            continue

        sorted_tuple = sorted(my_map.items(), key=lambda x:len(x[0]))
        appointment_values = ["%s for %s clinic visit" % (item[1], item[0]) for item in sorted_tuple if item[1] > 0]

        if len(appointment_values) > 1:
            msg_part = ", ".join(appointment_values[:-1]) + " and " + appointment_values[-1]
        else:
            msg_part = appointment_values[0]

        sent_to = 0
        for contact in Contact.active.filter(location=location, 
                                             types=get_clinic_worker_type()).\
            exclude(connection=None):
            msg = ("Hello %s, %s mothers are due for their clinic visits this week"
                   ", %s." % (contact.name, total, msg_part))
            if total == 1:
                single = str(filter(lambda x: x[1] > 0, sorted_tuple)[0][0])
                msg = ("Hello %s, 1 mother is due for her %s clinic visit this "
                   "week." % (contact.name, single))
            OutgoingMessage(contact.default_connection, msg).send()
            sent_to += 1

        for i, j in sorted_tuple:
            if j == 0:
                continue
            SentNotificationToClinic.objects.get_or_create(location=location, event_name=i, number=j, recipients=sent_to)
            SentNotificationToClinic.objects.get_or_create(location=location, event_name='Total', number=total, recipients=sent_to)
                       