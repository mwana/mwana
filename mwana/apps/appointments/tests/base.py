from __future__ import unicode_literals

import random
import string

from django.contrib.auth.models import User

from rapidsms.models import Connection, Backend
from rapidsms.tests.harness import RapidTest

from ..models import Timeline, TimelineSubscription, Milestone, Appointment, Notification, now


class AppointmentDataTestCase(RapidTest):
    "Helper methods for creating test data."

    def get_random_string(self, length=10):
        "Create a random string for generating test data."
        return ''.join(random.choice(string.ascii_letters) for x in range(length))

    def create_backend(self, **kwargs):
        "Create a dummy backend."
        defaults = {
            'name': self.get_random_string(),
        }
        defaults.update(kwargs)
        return Backend.objects.create(**defaults)

    def create_connection(self, **kwargs):
        "Create a dummy connection."
        defaults = {
            'identity': self.get_random_string(),
        }
        defaults.update(kwargs)
        if 'backend' not in defaults:
            defaults['backend'] = self.create_backend()
        return Connection.objects.create(**defaults)

    def create_timeline(self, **kwargs):
        "Create a dummy timeline."
        defaults = {
            'name': self.get_random_string(),
            'slug': self.get_random_string(),
        }
        defaults.update(kwargs)
        return Timeline.objects.create(**defaults)

    def create_timeline_subscription(self, **kwargs):
        "Create a dummy timeline subscription."
        defaults = {
            'pin': self.get_random_string(),
        }
        defaults.update(kwargs)
        if 'timeline' not in defaults:
            defaults['timeline'] = self.create_timeline()
        if 'connection' not in defaults:
            defaults['connection'] = self.create_connection()
        return TimelineSubscription.objects.create(**defaults)

    def create_milestone(self, **kwargs):
        "Create a dummy milestone."
        defaults = {
            'name': self.get_random_string(),
            'offset': random.randint(7, 365)
        }
        defaults.update(kwargs)
        if 'timeline' not in defaults:
            defaults['timeline'] = self.create_timeline()
        return Milestone.objects.create(**defaults)

    def create_appointment(self, **kwargs):
        "Create a dummy appointment."
        defaults = {
            'date': now().date(),
        }
        defaults.update(kwargs)
        if 'milestone' not in defaults:
            defaults['milestone'] = self.create_milestone()
        if 'subscription' not in defaults:
            defaults['subscription'] = self.create_timeline_subscription()
        return Appointment.objects.create(**defaults)

    def create_notification(self, **kwargs):
        "Create a dummy notification."
        defaults = {
            'message': self.get_random_string(),
        }
        defaults.update(kwargs)
        if 'appointment' not in defaults:
            defaults['appointment'] = self.create_appointment()
        return Notification.objects.create(**defaults)

    def create_user(self, username=None, password=None, email=None,
            user_permissions=None, groups=None, **kwargs):
        username = username or self.random_string(25)
        password = password or self.random_string(25)
        email = email or '{0}@example.com'.format(self.random_string(25))
        user = User.objects.create_user(username, email, password)
        if user_permissions:
            user.user_permissions = user_permissions
        if groups:
            user.groups = groups
        if kwargs:
            User.objects.filter(pk=user.pk).update(**kwargs)
        return User.objects.get(pk=user.pk)
