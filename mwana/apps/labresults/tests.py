import json
import datetime

from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse

from rapidsms.tests.scripted import TestScript

from mwana.apps.labresults.app import App
from mwana.apps.labresults import models as labresults


class TestApp(TestScript):
    apps = [App]
    
    def test_raw_result_entry(self):
        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='labresults',
                                      codename='add_rawresult')
        user.user_permissions.add(perm)
        self.client.login(username='adh', password='abc')
        data = {'varname': 'data'}
        now = datetime.datetime.now()
        response = self.client.post(reverse('accept_results'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(labresults.RawResult.objects.count(), 1)
        raw_result = labresults.RawResult.objects.get()
        self.assertEqual(raw_result.data, json.dumps(data))
        self.assertFalse(raw_result.processed)
        self.assertEqual(raw_result.date.year, now.year)
        self.assertEqual(raw_result.date.month, now.month)
        self.assertEqual(raw_result.date.day, now.day)
        self.assertEqual(raw_result.date.hour, now.hour)
    
    def test_raw_result_login_required(self):
        data = {'varname': 'data'}
        response = self.client.post(reverse('accept_results'), data)
        self.assertEqual(response.status_code, 401) # authorization required
        self.assertEqual(labresults.RawResult.objects.count(), 0)
    
    def test_raw_result_permission_required(self):
        User.objects.create_user(username='adh', email='', password='abc')
        self.client.login(username='adh', password='abc')
        data = {'varname': 'data'}
        response = self.client.post(reverse('accept_results'), data)
        self.assertEqual(response.status_code, 401) # authorization required
        self.assertEqual(labresults.RawResult.objects.count(), 0)
    
    def test_raw_result_post_required(self):
        response = self.client.get(reverse('accept_results'))
        self.assertEqual(response.status_code, 405) # method not supported

