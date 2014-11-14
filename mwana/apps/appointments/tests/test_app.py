from __future__ import unicode_literals

import datetime

from .base import AppointmentDataTestCase
from ..models import Appointment, Notification
from ..tasks import generate_appointments, send_appointment_notifications


class AppointmentAppTestCase(AppointmentDataTestCase):
    "Integration test for larger SMS workflow."

    def setUp(self):
        super(AppointmentAppTestCase, self).setUp()
        self.timeline = self.create_timeline(name='Test', slug='foo')
        self.milestone = self.create_milestone(timeline=self.timeline, offset=1)
        self.connection = self.lookup_connections('5555555555')[0]

    def test_join(self):
        "Join timeline then generate upcoming appointments."
        msg = self.receive('APPT NEW FOO 123', self.connection)
        reply = self.outbound.pop()
        self.assertTrue(reply.text.startswith('Thank you'))
        # Single appointment should be created
        generate_appointments()
        appointment = Appointment.objects.get(subscription__connection=self.connection, milestone=self.milestone)
        tomorrow = datetime.date.today() + datetime.timedelta(days=self.milestone.offset)
        self.assertEqual(tomorrow, appointment.date)

    def test_confirm_appointment(self):
        "Generate a notification and confirm an appointment."
        subscription = self.create_timeline_subscription(connection=self.connection, timeline=self.timeline)
        generate_appointments()
        send_appointment_notifications()
        reminder = self.outbound.pop()
        self.assertTrue(reminder.text.startswith('This is a reminder'))
        msg = self.receive('APPT CONFIRM FOO {0}'.format(subscription.pin), self.connection)
        reply = self.outbound.pop()
        self.assertTrue(reply.text.startswith('Thank you'))
        appointment = Appointment.objects.get(subscription__connection=self.connection, milestone=self.milestone)
        self.assertTrue(appointment.confirmed)

    def test_made_appointment(self):
        "Mark an appointment as seen."
        yesterday = datetime.date.today() - datetime.timedelta(days=self.milestone.offset)
        # Joined yesterday so appointment would be today
        subscription = self.create_timeline_subscription(
            connection=self.connection, timeline=self.timeline, start=yesterday)
        generate_appointments()
        send_appointment_notifications()
        reminder = self.outbound.pop()
        self.assertTrue(reminder.text.startswith('This is a reminder'))
        msg = self.receive('APPT STATUS FOO {0} SAW'.format(subscription.pin), self.connection)
        reply = self.outbound.pop()
        self.assertTrue(reply.text.startswith('Thank you'))
        appointment = Appointment.objects.get(subscription__connection=self.connection, milestone=self.milestone)
        self.assertEqual(Appointment.STATUS_SAW, appointment.status)

    def test_missed_appointment(self):
        "Mark an appointment as missed."
        yesterday = datetime.date.today() - datetime.timedelta(days=self.milestone.offset)
        # Joined yesterday so appointment would be today
        subscription = self.create_timeline_subscription(
            connection=self.connection, timeline=self.timeline, start=yesterday)
        generate_appointments()
        send_appointment_notifications()
        reminder = self.outbound.pop()
        self.assertTrue(reminder.text.startswith('This is a reminder'))
        msg = self.receive('APPT STATUS FOO {0} MISSED'.format(subscription.pin), self.connection)
        reply = self.outbound.pop()
        self.assertTrue(reply.text.startswith('Thank you'))
        appointment = Appointment.objects.get(subscription__connection=self.connection, milestone=self.milestone)
        self.assertEqual(Appointment.STATUS_MISSED, appointment.status)

    def test_join_then_quit(self):
        "Join a timeline then quit."
        msg = self.receive('APPT NEW FOO 123', self.connection)
        reply = self.outbound.pop()
        self.assertTrue(reply.text.startswith('Thank you'))
        msg = self.receive('APPT QUIT FOO 123', self.connection)
        reply = self.outbound.pop()
        self.assertTrue(reply.text.startswith('Thank you'))
        generate_appointments()
        # No appointments should be generated
        appointments = Appointment.objects.filter(subscription__connection=self.connection)
        self.assertEqual(0, appointments.count())

    def test_quit_reminders(self):
        "Don't send reminders for unsubscribed users."
        msg = self.receive('APPT NEW FOO 123', self.connection)
        reply = self.outbound.pop()
        self.assertTrue(reply.text.startswith('Thank you'))
        generate_appointments()
        msg = self.receive('APPT QUIT FOO 123', self.connection)
        reply = self.outbound.pop()
        self.assertTrue(reply.text.startswith('Thank you'))
        send_appointment_notifications()
        self.assertEqual(0, len(self.outbound), self.outbound)
        appointment = Appointment.objects.get(subscription__connection=self.connection, milestone=self.milestone)
        notifications = Notification.objects.filter(appointment=appointment)
        self.assertEqual(0, notifications.count())
