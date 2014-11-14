from __future__ import unicode_literals
from urllib import urlencode
from cStringIO import StringIO

from appointments.unicsv import UnicodeCSVReader

from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse

from ..models import Appointment
from .base import AppointmentDataTestCase


__all__ = ['AppointmentListViewTestCase', 'AppointmentExportViewTestCase']


class AppointmentViewTestCase(AppointmentDataTestCase):
    url_name = None
    perm_names = []
    url_args = []
    url_kwargs = {}
    get_kwargs = {}

    def setUp(self):
        super(AppointmentViewTestCase, self).setUp()
        self.username = 'testuser'
        self.password = 'password'
        self.permissions = self.get_permissions()
        self.user = self.create_user(self.username, self.password,
                user_permissions=self.permissions)
        self.client.login(username=self.username, password=self.password)

    def get_permissions(self, perm_names=None):
        """Returns a list of Permission objects corresponding to perm_names."""
        perm_names = perm_names if perm_names is not None else self.perm_names
        return [Permission.objects.filter(content_type__app_label=app_label,
                codename=codename)[0] for app_label, codename in perm_names]

    def _url(self, url_name=None, url_args=None, url_kwargs=None,
            get_kwargs=None):
        url_name = url_name or self.url_name
        url_args = self.url_args if url_args is None else url_args
        url_kwargs = self.url_kwargs if url_kwargs is None else url_kwargs
        get_kwargs = self.get_kwargs if get_kwargs is None else get_kwargs
        url = reverse(url_name, args=url_args, kwargs=url_kwargs)
        if get_kwargs:
            url = '{0}?{1}'.format(url, urlencode(get_kwargs))
        return url

    def _get(self, url_name=None, url_args=None, url_kwargs=None,
            get_kwargs=None, url=None, *args, **kwargs):
        """Convenience wrapper for self.client.get.

        If url is not given, it is built using url_name, url_args, and
        url_kwargs. Get parameters may be added from get_kwargs.
        """
        url = url or self._url(url_name, url_args, url_kwargs, get_kwargs)
        return self.client.get(url, *args, **kwargs)


class AppointmentListViewTestCase(AppointmentViewTestCase):
    url_name = 'appointment_list'
    perm_names = [('appointments', 'view_appointment')]

    def _extract(self, response):
        """Extract the information we're interested in from the context."""
        form = response.context['form']
        queryset = response.context['table'].data.queryset
        return queryset, form

    def test_no_permission(self):
        """Permission is required to get the Appointment list page."""
        self.user.user_permissions.all().delete()
        response = self._get()
        self.assertEquals(response.status_code, 302)  # redirect to login

    def test_no_appointments(self):
        """Retrieve the Appointment list when there are no appointments."""
        Appointment.objects.all().delete()
        response = self._get()
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 0)

    def test_appointment(self):
        """Retrieve the Appointment list when there is one Appointment."""
        report = self.create_appointment()
        response = self._get()
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.get(), report)

    def test_pagination(self):
        """The reports list should show 10 items per page."""
        for i in range(11):
            self.create_appointment()
        response = self._get(get_kwargs={'page': 2})
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 11)
        page = response.context['table'].page
        self.assertEquals(page.object_list.data.count(), 1)

    def test_filter_subscription_timeline(self):
        """Reports should be filtered by timeline."""
        timeline = self.create_timeline()
        subscription = self.create_timeline_subscription(timeline=timeline)
        appt = self.create_appointment(subscription=subscription)
        self.create_appointment()
        response = self._get(get_kwargs={'subscription__timeline': timeline.id})
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.get(), appt)

    def test_filter_bad_subscription_timeline(self):
        """Form does no validation on timeline, but no results returned."""
        timeline = self.create_timeline()
        subscription = self.create_timeline_subscription(timeline=timeline)
        self.create_appointment(subscription=subscription)
        response = self._get(get_kwargs={'subscription__timeline': 10})
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 0)
        self.assertTrue('subscription__timeline' in form.errors)

    def test_filter_status(self):
        """Reports should be filtered by status."""
        params = {'status': Appointment.STATUS_MISSED}
        appt = self.create_appointment(**params)
        self.create_appointment()
        response = self._get(get_kwargs=params)
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.get(), appt)

    def test_filter_bad_status(self):
        """Form has error & no results returned if invalid status is given."""
        self.create_appointment()
        response = self._get(get_kwargs={'status': 7})
        self.assertEquals(response.status_code, 200)
        queryset, form = self._extract(response)
        self.assertEquals(queryset.count(), 0)
        self.assertTrue('status' in form.errors)


class AppointmentExportViewTestCase(AppointmentViewTestCase):
    url_name = 'csv_appointment_list'
    perm_names = [('appointments', 'view_appointment')]

    def _extract(self, response):
        reader = UnicodeCSVReader(StringIO(response.content))
        return [line for line in reader]

    def _check_appointment(self, response, *appts):
        self.assertEquals(response.status_code, 200)
        csv = self._extract(response)
        self.assertEquals(len(csv), 1 + len(appts))  # include headers row

        num_columns = 8
        headers, data = csv[0], csv[1:]
        self.assertEquals(len(headers), num_columns)
        for line in data:
            self.assertEquals(len(line), num_columns)

    def test_no_permissions(self):
        """Permission is required to export a Appointment list."""
        self.user.user_permissions.all().delete()
        response = self._get()
        self.assertEquals(response.status_code, 302)  # redirect to login

    def test_no_appointments(self):
        """Export reports list when there are no reports."""
        Appointment.objects.all().delete()
        response = self._get()
        self._check_appointment(response)

    def test_appointment(self):
        """Export reports list when there is one Appointment."""
        report = self.create_appointment()
        response = self._get()
        self._check_appointment(response, report)

    def test_filter_subscription_timeline(self):
        """Reports export should be filtered by timeline."""
        timeline = self.create_timeline()
        subscription = self.create_timeline_subscription(timeline=timeline)
        appt = self.create_appointment(subscription=subscription)
        self.create_appointment()
        response = self._get(get_kwargs={'subscription__timeline': timeline.id})
        self._check_appointment(response, appt)

    def test_filter_bad_subscription_timeline(self):
        """Invalid status causes redirect to regular list view."""
        self.create_appointment()
        response = self._get(get_kwargs={'status': 'bad'}, follow=True)
        correct_url = reverse('appointment_list') + '?status=bad'
        self.assertRedirects(response, correct_url)
        queryset = response.context['table'].data.queryset
        form = response.context['form']
        self.assertEquals(queryset.count(), 0)
        self.assertTrue('status' in form.errors)

    def test_filter_status(self):
        """Reports export should be filtered by status."""
        params = {'status': Appointment.STATUS_MISSED}
        appt = self.create_appointment(**params)
        self.create_appointment()
        response = self._get(get_kwargs=params)
        self._check_appointment(response, appt)

    def test_filter_bad_status(self):
        """Invalid status causes redirect to regular list view."""
        self.create_appointment()
        response = self._get(get_kwargs={'status': 'bad'}, follow=True)
        correct_url = reverse('appointment_list') + '?status=bad'
        self.assertRedirects(response, correct_url)
        queryset = response.context['table'].data.queryset
        form = response.context['form']
        self.assertEquals(queryset.count(), 0)
        self.assertTrue('status' in form.errors)
