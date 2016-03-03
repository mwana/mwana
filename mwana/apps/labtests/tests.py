# vim: ai ts=4 sts=4 et sw=4
import time
import json

import datetime
import mwana.const as const
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings
from mwana.apps.labtests import models as labtests
from mwana.apps.labtests.models import Result
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from rapidsms.models import Connection, Contact
from rapidsms.tests.scripted import TestScript
from mwana.apps.labtests import tasks
from mwana.apps.labtests.testdata.payloads import INITIAL_PAYLOAD

import random


class LabtestsSetUp(TestScript):

    def _result_text(self):
        """
        Returns the appropriate display value for viral load results as it would
        appear in an SMS.
        """
        results_text = getattr(settings, 'RESULTS160_RESULT_DISPLAY', {})
        results = {'detected': results_text.get('P', 'Detected'),
                   'not_detected': results_text.get('N', 'NotDetected')}
        return results

    def setUp(self):
        # this call is required if you want to override setUp
        super(LabtestsSetUp, self).setUp()
        self.type = LocationType.objects.get_or_create(singular="clinic", plural="clinics", slug=const.CLINIC_SLUGS[2])[0]
        self.type1 = LocationType.objects.get_or_create(singular="district", plural="districts", slug="districts")[0]        
        self.type2 = LocationType.objects.get_or_create(singular="province", plural="provinces", slug="provinces")[0]        
        self.luapula = Location.objects.create(type=self.type2, name="Luapula Province", slug="luapula")
        self.mansa = Location.objects.create(type=self.type1, name="Mansa District", slug="mansa", parent = self.luapula)
        self.samfya = Location.objects.create(type=self.type1, name="Samfya District", slug="samfya", parent = self.luapula)
        self.clinic = Location.objects.create(type=self.type, name="Mibenge Clinic", slug="402029", parent = self.samfya, send_live_results=True)
        self.mansa_central = Location.objects.create(type=self.type, name="Central Clinic", slug="403012", parent = self.mansa, send_live_results=True)
        # clinic for send_live_results = True
        self.clinic_live_results_true = Location.objects.create(type=self.type, name="LiveResultsTrue Clinic", slug="403010", parent = self.mansa, send_live_results=True)
        # clinic for send_live_results = False
        self.clinic_live_results_false = Location.objects.create(type=self.type, name="LiveResultsFalse Clinic", slug="403011", parent = self.mansa, send_live_results=False)
        
        self.support_clinic = Location.objects.create(type=self.type, name="Support Clinic", slug="spt")
        # this gets the backend and connection in the db
        script = "clinic_worker > hello world"
        self.runScript(script)
        connection = Connection.objects.get(identity="clinic_worker")
        
        self.contact = Contact.objects.create(alias="banda", name="John Banda", 
                                              location=self.clinic, pin="4567")
        self.contact.types.add(const.get_clinic_worker_type())
                                
        connection.contact = self.contact
        connection.save()
        
        # create another one
        self.other_contact = Contact.objects.create(alias="mary", name="Mary Phiri", 
                                                    location=self.clinic, pin="6789")
        self.other_contact.types.add(const.get_clinic_worker_type())
        
        Connection.objects.create(identity="other_worker", backend=connection.backend, 
                                  contact=self.other_contact)
        connection.save()

        # create another worker for a different clinic
        self.central_clinic_worker = Contact.objects.create(alias="jp", name="James Phiri",
                                                    location=self.mansa_central, pin="1111")
        self.central_clinic_worker.types.add(const.get_clinic_worker_type())

        Connection.objects.create(identity="central_clinic_worker", backend=connection.backend,
                                  contact=self.central_clinic_worker)
        connection.save()
        
        # create a worker for the live_results_true clinic
        self.true_clinic_worker = Contact.objects.create(alias="jbt", name="John Banda",
                                        location=self.clinic_live_results_true, pin="1001")
        self.true_clinic_worker.types.add(const.get_clinic_worker_type())
        
        Connection.objects.create(identity="true_clinic_worker", backend=connection.backend,
                                    contact=self.true_clinic_worker)
        
        # create a worker for the live_results_false clinic
        self.false_clinic_worker = Contact.objects.create(alias="jbf", name="John Banda",
                                        location=self.clinic_live_results_false, pin="0110")
        self.false_clinic_worker.types.add(const.get_clinic_worker_type())
        
        Connection.objects.create(identity="false_clinic_worker", backend=connection.backend,
                                    contact=self.false_clinic_worker)

        # create support staff
        self.support_contact = Contact.objects.create(alias="ha1", name="Help Admin",
                                                    location=self.support_clinic, pin="1111", is_help_admin=True)
        self.support_contact.types.add(const.get_clinic_worker_type())

        Connection.objects.create(identity="support_contact", backend=connection.backend,
                                  contact=self.support_contact)
        connection.save()

        # create second support staff
        self.support_contact2 = Contact.objects.create(alias="ha2", name="Help Admin2",
                                                    location=self.support_clinic, pin="2222", is_help_admin=True)
        self.support_contact2.types.add(const.get_clinic_worker_type())

        Connection.objects.create(identity="support_contact2", backend=connection.backend,
                                  contact=self.support_contact2)
        connection.save()

    def tearDown(self):
        # this call is required if you want to override tearDown
        super(LabtestsSetUp, self).tearDown()
        try:
            self.clinic.delete()
            self.type.delete()
            self.client.logout()
        except:
            pass
            #TODO catch specific exception

    def testBootstrap(self):
        contact = Contact.objects.get(id=self.contact.id)
        self.assertEqual("clinic_worker", contact.default_connection.identity)
        self.assertEqual(self.clinic, contact.location)
        self.assertEqual("4567", contact.pin)
        self.assertTrue(const.get_clinic_worker_type() in contact.types.all())


class TestApp(LabtestsSetUp):
        
    def testUnregisteredCheck(self):
        script = """
            unknown_user > VL RESULTS
            unknown_user < Sorry you must be registered with a clinic to check results. To register, send JOIN <TYPE> <LOCATION CODE> <NAME> <PIN CODE>
        """
        self.runScript(script)
        
    def testCheckResultsNone(self):
        script = """
            clinic_worker > VL RESULTS
            clinic_worker < Hello John Banda. There are no new test results for Mibenge Clinic right now. We'll let you know as soon as more results are available.
    """
        self.runScript(script)

    def testResultsPIN(self):
        # NOTE: this test is failing and I'm not sure why.
        # It works fine in the message tester.
        
        res2, res1, res3 = self._bootstrap_results()
        # initiate a test and before sending a correct PIN try a bunch 
        # of different things.
        # some messages should trigger a PIN wrong answer, others shouldn't
        script = """
            clinic_worker > VL RESULTS
            clinic_worker < Hello %(name)s. We have %(count)s viral load test results ready for you. Please reply to this SMS with your pin code to retrieve these results.
            clinic_worker > 55555
            clinic_worker < Sorry, that was not the correct pin code. Your pin code is a 4-digit number like 1234. If you forgot your pin code, reply with keyword 'HELP'
            clinic_worker > VL RESULTS
            clinic_worker < Hello %(name)s. We have %(count)s viral load test results ready for you. Please reply to this SMS with your pin code to retrieve these results.
            clinic_worker > here's some stuff that you won't understand
            clinic_worker < Sorry, that was not the correct pin code. Your pin code is a 4-digit number like 1234. If you forgot your pin code, reply with keyword 'HELP'
            clinic_worker > %(code)s
            clinic_worker < Thank you! Here are your results: **** %(id1)s;%(res1)s. **** %(id2)s;%(res2)s. **** %(id3)s;%(res3)s
            +260977212112 < Your appointment is due at Mibenge Clinic. Bring your referral letter with you to this appointment. If you got this msg by mistake please ignore
                clinic_worker < Please record these results in your clinic records and promptly delete them from your phone. Thank you again %(name)s!
            """ % {"name": self.contact.name, "count": 3, "code": "4567",
            "id1": res1.requisition_id, "res1": res1.get_result_text(),
            "id2": res2.requisition_id, "res2": res2.get_result_text(),
            "id3": res3.requisition_id, "res3": res3.get_result_text()}
        
        self.runScript(script)
        
        
    def testCheckResultsWorkflow(self):
        """Tests the "check" functionality"""
        
        # Save some results
        res2, res1, res3 = self._bootstrap_results()
        
        # These would be automatically sent by a scheduled task, but we
        # also support querying them via these magic keywords
        script = """
            clinic_worker > VL RESULTS
            clinic_worker < Hello %(name)s. We have %(count)s viral load test results ready for you. Please reply to this SMS with your pin code to retrieve these results.
        """ % {"name": self.contact.name, "count": 3}
        self.runScript(script)
        for res in [labtests.Result.objects.get(id=res.id)
                    for res in [res1, res2, res3]]:
            self.assertEqual("notified", res.notification_status)

        script = """
            clinic_worker > %(code)s
        clinic_worker < Thank you! Here are your results: **** %(id1)s;%(res1)s. **** %(id2)s;%(res2)s. **** %(id3)s;%(res3)s
        +260977212112 < Your appointment is due at Mibenge Clinic. Bring your referral letter with you to this appointment. If you got this msg by mistake please ignore
        clinic_worker < Please record these results in your clinic records and promptly delete them from your phone. Thank you again %(name)s!
        """ % {"name": self.contact.name, "code": "4567",
        "id1": res1.requisition_id, "res1": res1.get_result_text(),
        "id2": res2.requisition_id, "res2": res2.get_result_text(),
        "id3": res3.requisition_id, "res3": res3.get_result_text()}

        self.runScript(script)
        self.assertEqual(Result.objects.filter(participant_informed=1).count(), 1)
        
        for res in [labtests.Result.objects.get(id=res.id)
                    for res in [res1, res2, res3]]:
            self.assertEqual("sent", res.notification_status)
    
    def _bootstrap_results(self):
        results = labtests.Result.objects.all()
        res1 = results.create(requisition_id="%s-0001-1" % self.clinic.slug,
                              clinic=self.clinic, result="100",result_unit='m/L',
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today() - datetime.timedelta(days=3),
                              notification_status="new", sample_id='1')

        res2 = results.create(requisition_id="0002", clinic=self.clinic,
                              result="200", result_unit = 'm/L',
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today() - datetime.timedelta(days=2),
                              notification_status="new", sample_id='2')

        res3 = results.create(requisition_id="%s-0003-1" % self.clinic.slug,
                              clinic=self.clinic, result="300", result_unit = 'm/L',
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new", sample_id='3',
                              phone='+260977212112')

        return [res1, res2, res3]


class TestResultsAcceptor(LabtestsSetUp):
    """
    Tests processing of payloads
    """

    def _post_json(self, url, data):
        if not isinstance(data, basestring):
            data = json.dumps(data)
        return self.client.post(url, data, content_type='text/json')
    
    def test_payload_simple_entry(self):
        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='labtests',
                                      codename='add_payload')
        user.user_permissions.add(perm)
        self.client.login(username='adh', password='abc')
        data = {'varname': 'data'}
        now = datetime.datetime.now()
        response = self._post_json(reverse('labtests:accept_results'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(labtests.Payload.objects.count(), 1)
        payload = labtests.Payload.objects.get()
        self.assertEqual(payload.raw, json.dumps(data))
        self.assertTrue(payload.parsed_json)
        self.assertFalse(payload.validated_schema)
        self.assertEqual(user, payload.auth_user)
        self.assertEqual(payload.incoming_date.year, now.year)
        self.assertEqual(payload.incoming_date.month, now.month)
        self.assertEqual(payload.incoming_date.day, now.day)
        self.assertEqual(payload.incoming_date.hour, now.hour)

    def test_payload_complex_entry(self):
        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='labtests',
                                      codename='add_payload')
        type = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        Location.objects.create(name='Clinic', slug='202020',
                                type=type)
        user.user_permissions.add(perm)
        self.client.login(username='adh', password='abc')
        data = {
            "source": "ndola/arthur-davison", 
            "now": "2010-04-22 10:30:00", 
            "logs": [
                {
                    "msg": "booting daemon...", 
                    "lvl": "INFO", 
                    "at": "2010-04-22 07:18:03,140"
                }, 
                {
                    "msg": "archiving 124 records", 
                    "lvl": "INFO", 
                    "at": "2010-04-22 09:18:23,248"
                }
            ], 
            "samples": [
                {
                    "coll_on": "2010-03-31", 
                    "hw": "JANE SMITH", 
                    "mother_age": 19, 
                    "result_detail": None, 
                    "sync": "new", 
                    "sex": "f", 
                    "result": "negative", 
                    "recv_on": "2010-04-08", 
                    "fac": 2020200, 
                    "id": "10-09999", 
                    "hw_tit": "NURSE", 
                    "pat_id": "", 
                    "dob": "2010-02-08", 
                    "proc_on": "2010-04-11", 
                    "child_age": 3,
                    "result_unit": "p/mL",
                    "verified": False
                }, 
                {
                    "coll_on": "2010-03-25", 
                    "hw": "JENNY HOWARD", 
                    "mother_age": 41, 
                    "result_detail": None, 
                    "sync": "new", 
                    "sex": "f", 
                    "result": "negative", 
                    "recv_on": "2010-04-11", 
                    "fac": 2020200, 
                    "id": "10-09998", 
                    "hw_tit": "AMM", 
                    "pat_id": "1029023412", 
                    "dob": "2009-03-30", 
                    "proc_on": "2010-04-13", 
                    "child_age": 8,
                    "result_unit": "p/ML",
                    "verified": True,
                    "guspec": 'DLU0026F-02',
                    'province': '2',
                    'district': '207',
                    'constit': '29',
                    'ward': '3',
                    'csa': '8',
                    'sea': '2',
                    'test_type': 'vl',
                }, 
                {
                    "coll_on": "2010-04-08", 
                    "hw": "MOLLY", 
                    "mother_age": 31, 
                    "result_detail": None, 
                    "sync": "new", 
                    "sex": "f", 
                    "result": "negative", 
                    "recv_on": "2010-04-15", 
                    "fac": 2020200, 
                    "id": "10-09997", 
                    "hw_tit": "ZAN", 
                    "pat_id": "212987", 
                    "dob": "2010-01-12", 
                    "proc_on": "2010-04-17", 
                    "child_age": 4,
                    "result_unit": "p/mL",
                    "verified": False
                }
            ]
        }
        now = datetime.datetime.now()
        response = self._post_json(reverse('labtests:accept_results'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(labtests.Payload.objects.count(), 1)
        payload = labtests.Payload.objects.get()
        self.assertEqual(payload.raw, json.dumps(data))
        self.assertTrue(payload.parsed_json)
        self.assertTrue(payload.validated_schema)
        self.assertEqual(user, payload.auth_user)
        self.assertEqual(payload.incoming_date.year, now.year)
        self.assertEqual(payload.incoming_date.month, now.month)
        self.assertEqual(payload.incoming_date.day, now.day)
        self.assertEqual(payload.incoming_date.hour, now.hour)

        self.assertEqual(labtests.Result.objects.count(), 2)
        result1 = labtests.Result.objects.get(sample_id="10-09998")
        result2 = labtests.Result.objects.get(sample_id="10-09997")
        # 10-09999 will not make it in because it's missing a pat_id
        self.assertEqual(result1.payload, payload)
        self.assertEqual(result2.payload, payload)
        self.assertTrue(result1.verified)
        self.assertFalse(result2.verified)
        self.assertEqual(labtests.Result.objects.filter(sample_id="10-09998", guspec="DLU0026F-02", province='2', district='207', constit='29', ward='3', csa='8', sea='2').count(), 1)
        self.assertEqual(labtests.Result.objects.filter(sample_id="10-09998", test_type='vl').count(), 1)


    def test_payload_missing_fac(self):
        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='labtests',
                                      codename='add_payload')
        type = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        Location.objects.create(name='Clinic', slug='202020',
                                type=type)
        user.user_permissions.add(perm)
        self.client.login(username='adh', password='abc')
        data = {
            "source": "ndola/arthur-davison", 
            "now": "2010-04-22 10:30:00", 
            "logs": [
                {
                    "msg": "booting daemon...", 
                    "lvl": "INFO", 
                    "at": "2010-04-22 07:18:03,140"
                }
            ], 
            "samples": [
                {
                    "coll_on": "2010-03-31", 
                    "hw": "JANE SMITH", 
                    "mother_age": 19, 
                    "result_detail": None, 
                    "sync": "new", 
                    "sex": "f", 
                    "result": "negative", 
                    "recv_on": "2010-04-08", 
                    "fac": 0, 
                    "id": "10-09999", 
                    "hw_tit": "NURSE", 
                    "pat_id": "1234", 
                    "dob": "2010-02-08", 
                    "proc_on": "2010-04-11", 
                    "child_age": 3
                }
            ]
        }
        now = datetime.datetime.now()
        response = self._post_json(reverse('labtests:accept_results', current_app='labtests'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(labtests.Payload.objects.count(), 1)
        payload = labtests.Payload.objects.get()
        self.assertEqual(payload.raw, json.dumps(data))
        self.assertTrue(payload.parsed_json)
        self.assertTrue(payload.validated_schema)
        self.assertEqual(labtests.Result.objects.count(), 1)

    def test_payload_login_required(self):
        data = {'varname': 'data'}
        response = self._post_json(reverse('labtests:accept_results', current_app='labtests'), data)
        self.assertEqual(response.status_code, 401) # authorization required
        self.assertEqual(labtests.Payload.objects.count(), 0)
    
    def test_payload_permission_required(self):
        User.objects.create_user(username='adh', email='', password='abc')
        self.client.login(username='adh', password='abc')
        data = {'varname': 'data'}
        response = self._post_json(reverse('labtests:accept_results', current_app='labtests'), data)
        self.assertEqual(response.status_code, 401) # authorization required
        self.assertEqual(labtests.Payload.objects.count(), 0)
    
    def test_payload_post_required(self):
        response = self.client.get(reverse('labtests:accept_results', current_app='labtests'))
        self.assertEqual(response.status_code, 405) # method not supported

    def create_payload_auther_login(self):
        """
        Tests sending of notifications for previously sent results but later
        change in locaion.
        """

        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='labtests',
                                      codename='add_payload')
        user.user_permissions.add(perm)
        self.client.login(username='adh', password='abc')
    
    def test_send_results_notification(self):
        """
        Tests sending of notifications for new results.
        """
        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='labtests',
                                      codename='add_payload')
        user.user_permissions.add(perm)
        self.client.login(username='adh', password='abc')

        # get results from a payload
        self._post_json(reverse('labtests:accept_results'), INITIAL_PAYLOAD)

        # The number of results records should be 3
        self.assertEqual(labtests.Result.objects.count(), 4)
        self.assertEqual(labtests.Result.objects.filter(test_type=const.get_viral_load_type()).count(), 3)
        self.assertEqual(labtests.Result.objects.exclude(phone=None).exclude(phone='').count(), 1)
        self.assertEqual(labtests.Result.objects.filter(clinic=self.clinic).count(), 4)

        time.sleep(.2)
        # start router and send a notification
        self.startRouter()
        tasks.send_vl_results_notification(self.router)

        # Get all the messages sent
        msgs = self.receiveAllMessages()
        self.stopRouter()
        self.assertEqual(2, len(msgs))
        
        msg1 = "Hello Mary Phiri. We have 3 viral load test results ready for you. Please reply to this SMS with your pin code to retrieve these results."
        msg2 = "Hello John Banda. We have 3 viral load test results ready for you. Please reply to this SMS with your pin code to retrieve these results."

        self.assertTrue(msg1 in (msgs[0].text, msgs[1].text ),
        "Following message was not sent:\n%s" % msg1)
        self.assertTrue(msg2 in (msgs[0].text, msgs[1].text ),
        "Following message was not sent:\n%s" % msg2)
        self.assertEqual(2,len(msgs))

        time.sleep(.1)
        # start router and send a notification
        self.startRouter()
        tasks.send_vl_results_notification(self.router)

        # Get all the messages sent
        msgs = self.receiveAllMessages()
        
        self.assertEqual(2,len(msgs))
        self.assertEqual(msg2,msgs[0].text)
        self.assertEqual(msg1,msgs[1].text)

        self.assertEqual(3, Result.objects.filter(notification_status='notified',
                            ).count())
               
        self.assertEqual(3, Result.objects.filter(notification_status='notified',
                            ).exclude(date_of_first_notification=None).count())

        self.assertEqual(0, Result.objects.filter(notification_status='sent',
                            result_sent_date=None).count())
        self.assertEqual(0, Result.objects.filter(
                            arrival_date=None).exclude(result=None).count())
        time.sleep(1)
        self.stopRouter()

        script = """
            other_worker > 6789
            other_worker < Thank you! Here are your results: **** 1029023412;200p/mL. **** 78;100p/mL. **** 212987;300p/mL
            +260977212112 < Your appointment is due at Mibenge Clinic. Bring your referral letter with you to this appointment. If you got this msg by mistake please ignore
            clinic_worker < Mary Phiri has collected these results
            other_worker < Please record these results in your clinic records and promptly delete them from your phone. Thank you again Mary Phiri!
        """
        time.sleep(1)
        self.runScript(script)
