import datetime

from celery import task

from django.db.models import Q, F
from django.utils.translation import ugettext_lazy as _
try:
    from django.utils.timezone import now
except ImportError:  # Django < 1.4
    now = datetime.datetime.now

from rapidsms.router import send

from mwana.apps.appointments.models import (TimelineSubscription, Appointment,
                                            Notification)

APPT_REMINDER = _('This is a reminder for your upcoming appointment'
                  ' on %(date)s. Please confirm.')


@task()
def generate_appointments(days=14):
    """
    Task to create Appointment instances based on current TimelineSubscriptions

    Arguments:
    days: The number of upcoming days to create Appointments for
    """
    start = datetime.date.today()
    end = start + datetime.timedelta(days=days)

    subs = TimelineSubscription.objects.filter(
        Q(end__gte=now()) | Q(end__isnull=True))

    for sub in subs:
        for milestone in sub.timeline.milestones.all():
            milestone_date = sub.start.date() + datetime.timedelta(
                days=milestone.offset)
            # skip weekends for appointments, move to pandas?
            if milestone_date.weekday() == 5:
                milestone_date = milestone_date - datetime.timedelta(days=1)
            elif milestone_date.weekday() == 6:
                milestone_date = milestone_date + datetime.timedelta(days=1)
            #Create appointment(s) for this subscription within the task window
            if start <= milestone_date <= end:
                appt, created = Appointment.objects.get_or_create(
                    subscription=sub,
                    milestone=milestone,
                    date=milestone_date
                )


@task()
def send_appointment_notifications(days=7):
    """
    Task to send reminders notifications for upcoming Appointment

    Arguments:
    days: The number of upcoming days to filter upcoming Appointments
    """
    start = datetime.date.today()
    end = start + datetime.timedelta(days=days)
    blacklist = [Notification.STATUS_SENT, Notification.STATUS_CONFIRMED,
                 Notification.STATUS_MANUAL]
    appts = Appointment.objects.filter(
        # Join subscriptions that haven't ended
        Q(Q(subscription__connection__timelines__end__gte=now()) | Q(
            subscription__connection__timelines__end__isnull=True)),
        subscription__connection__timelines__timeline=F('milestone__timeline'),
        # Filter appointments in range
        date__range=(start, end),
    ).exclude(notifications__status__in=blacklist)
    for appt in appts:
        # TODO: customize per app messages here.
        msg = APPT_REMINDER % {'date': appt.date}
        send(msg, appt.subscription.connection)
        Notification.objects.create(appointment=appt,
                                    status=Notification.STATUS_SENT,
                                    sent=now(),
                                    message=msg)
