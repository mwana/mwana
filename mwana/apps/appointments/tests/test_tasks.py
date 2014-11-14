from __future__ import unicode_literals

import datetime

from .base import AppointmentDataTestCase, Appointment, Milestone, Notification, now
from ..tasks import generate_appointments, send_appointment_notifications, APPT_REMINDER


class GenerateAppointmentsTestCase(AppointmentDataTestCase):
    "Task to generate future appointments"

    def setUp(self):
        self.timeline = self.create_timeline(name='Test', slug='foo')
        self.offsets = [1, 3, 7, 14, 30]
        for offset in self.offsets:
            self.create_milestone(name='{0} day(s)'.format(offset), offset=offset, timeline=self.timeline)
        self.sub = self.create_timeline_subscription(timeline=self.timeline)
        self.cnx = self.sub.connection

    def test_generate_appointments(self):
        "Test the default task"
        self.assertEqual(0, Appointment.objects.filter(subscription__connection=self.cnx).count())
        generate_appointments()
        self.assertEqual(4, Appointment.objects.filter(subscription__connection=self.cnx).count())

    def test_generate_appointments_already_exists(self):
        "The task should generate no appointments if the series already exists for the user"
        self.cnx = self.sub.connection
        for offset in self.offsets:
            date = now() + datetime.timedelta(days=offset)
            milestone = Milestone.objects.get(offset=offset)
            self.create_appointment(subscription=self.sub, date=date, milestone=milestone)
        self.assertEqual(5, Appointment.objects.filter(subscription__connection=self.cnx).count())
        generate_appointments()
        self.assertEqual(5, Appointment.objects.filter(subscription__connection=self.cnx).count())

    def test_generate_appointments_out_of_range(self):
        "The task should generate no appointments if the milestones are out of range"
        Milestone.objects.all().delete()
        offsets = [15, 17]
        for offset in offsets:
            self.create_milestone(name='{0} day(s)'.format(offset), offset=offset, timeline=self.timeline)
        self.assertEqual(0, Appointment.objects.filter(subscription__connection=self.cnx).count())
        generate_appointments()
        self.assertEqual(0, Appointment.objects.filter(subscription__connection=self.cnx).count())

    def test_generate_appointments_multiple_subscriptions(self):
        "The task should generate appointments for all applicable subscriptions"
        self.assertEqual(0, Appointment.objects.all().count())
        self.create_timeline_subscription(timeline=self.timeline)
        generate_appointments()
        self.assertEqual(8, Appointment.objects.all().count())

    def test_generate_appointments_for_n_days(self):
        "The task should generate appointments when supplied N days as an argument"
        self.assertEqual(0, Appointment.objects.all().count())
        generate_appointments(30)
        self.assertEqual(5, Appointment.objects.all().count())


class SendAppointmentNotificationsTestCase(AppointmentDataTestCase):
    "Task to send notifications for upcoming Appointments"

    def setUp(self):
        self.backend = self.create_backend(name='mockbackend')
        self.cnx = self.create_connection(backend=self.backend)
        self.timeline = self.create_timeline()
        self.subscription = self.create_timeline_subscription(connection=self.cnx, timeline=self.timeline)
        self.appointment = self.create_appointment(subscription=self.subscription)

    def create_milestone(self, **kwargs):
        "Ensure milestones are created on the default timeline."
        kwargs['timeline'] = self.timeline
        return super(SendAppointmentNotificationsTestCase, self).create_milestone(**kwargs)

    def test_send_notifications(self):
        "Test the default task"
        self.assertEqual(0, Notification.objects.filter(appointment=self.appointment).count())
        send_appointment_notifications()
        self.assertEqual(1, Notification.objects.filter(appointment=self.appointment).count())
        msg = APPT_REMINDER % {'date': self.appointment.date}
        self.assertEqual(self.outbound[0].text, msg)
        self.assertEqual(self.outbound[0].connection, self.cnx)

    def test_send_notifications_not_notified(self):
        "The task should generate no notifications if a reminder has already been sent"
        self.create_notification(appointment=self.appointment, status=1)
        self.assertEqual(1, Notification.objects.filter(appointment=self.appointment).count())
        send_appointment_notifications()
        self.assertEqual(1, Notification.objects.filter(appointment=self.appointment).count())
        self.assertEqual(0, len(self.outbound))

    def test_send_notifications_out_of_range(self):
        "The task should generate no notifications if the appointment(s) are out of range"
        self.appointment.date = self.appointment.date + datetime.timedelta(days=10)
        self.appointment.save()
        self.assertEqual(0, Notification.objects.filter(appointment=self.appointment).count())
        send_appointment_notifications()
        self.assertEqual(0, Notification.objects.filter(appointment=self.appointment).count())
        self.assertEqual(0, len(self.outbound))

    def test_send_notifications_multiple_users(self):
        "The task should generate notifications for all applicable appointments"
        self.cnx2 = self.create_connection(identity='johndoe', backend=self.backend)
        self.sub2 = self.create_timeline_subscription(connection=self.cnx2, timeline=self.timeline)
        self.create_appointment(subscription=self.sub2)
        self.assertEqual(0, Notification.objects.all().count())
        send_appointment_notifications()
        self.assertEqual(2, Notification.objects.all().count())
        self.assertEqual(2, len(self.outbound))

    def test_send_notifications_for_n_days(self):
        "The task should generate appointments when supplied N days as an argument"
        self.create_appointment(subscription=self.subscription, date=now() + datetime.timedelta(days=10))
        self.assertEqual(0, Notification.objects.all().count())
        send_appointment_notifications(30)
        self.assertEqual(2, Notification.objects.all().count())
        self.assertEqual(2, len(self.outbound))
