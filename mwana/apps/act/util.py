# vim: ai ts=4 sts=4 et sw=4
import random

from mwana.apps.act.models import HistoricalEvent
from mwana.apps.act.models import ReminderMessagePreference
from mwana.apps.act.models import Appointment


def get_historical_event_message(p_date):
    events = HistoricalEvent.objects.filter(date__month=p_date.month).filter(date__day=p_date.day)
    if events:
        event = random.choice(events)
        return event.did_you_know_message()
    else:
        return HistoricalEvent.mock_message(p_date)


def get_preferred_message_template(client, visit_type):
        try:
            rmp = ReminderMessagePreference.objects.get(client=client, visit_type=visit_type)
            # @type rmp ReminderMessagePreference
            return rmp.get_message_text()
        except ReminderMessagePreference.DoesNotExist:
            return None
        except ReminderMessagePreference.MultipleObjectsReturned:
            return None


def get_preferred_lab_message_template(client):
        return get_preferred_message_template(client, Appointment.get_lab_type())


def get_preferred_pharmacy_message_template(client):
        return get_preferred_message_template(client, Appointment.get_pharmacy_type())

