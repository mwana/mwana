import datetime

from mwana.apps.reminders import models as reminders


def send_notification(patient, notification):
    print 'Sending %s notification to %s' % (notification, patient)


def send_notifications():
    for notification in reminders.Notification.objects.all():
        date = datetime.datetime.now() -\
               datetime.timedelta(days=notification.num_days)
        # TODO: add ability to send reminder emails ahead of actual appointment
        patients = reminders.PatientEvent.objects.filter(
            event=notification.event,
            date__lte=date,
            sent_notifications__isnull=True
        )
        for patient in patients:
            send_notification(patient, notification)
