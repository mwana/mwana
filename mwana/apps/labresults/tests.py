import json

import datetime
import mwana.const as const
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from mwana.apps.labresults import models as labresults
from mwana.apps.labresults.app import App
from mwana.apps.labresults.mocking import get_fake_results
from mwana.apps.labresults.models import Result, SampleNotification
from mwana.apps.stringcleaning.app import App as cleaner_App
from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.contrib.locations.models import Location
from rapidsms.contrib.locations.models import LocationType
from rapidsms.models import Connection
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript


class TestApp(TestScript):
    apps = (cleaner_App, handler_app, App)
    
    def setUp(self):
        # this call is required if you want to override setUp
        super(TestApp, self).setUp()
        self.type = LocationType.objects.get_or_create(singular="clinic", plural="clinics", slug="clinics")[0]
        self.clinic = Location.objects.create(type=self.type, name="Mibenge Clinic", slug="mib")
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
        

    def tearDown(self):
        # this call is required if you want to override tearDown
        super(TestApp, self).tearDown()
        self.clinic.delete()
        self.type.delete()
    
    def testBootstrap(self):
        contact = Contact.objects.get(id=self.contact.id)
        self.assertEqual("clinic_worker", contact.default_connection.identity)
        self.assertEqual(self.clinic, contact.location)
        self.assertEqual("4567", contact.pin)
        self.assertTrue(const.get_clinic_worker_type() in contact.types.all())
    
    testReportResults = """
            clinic_worker > SENT 33
            clinic_worker < Hello John Banda! We received your notification that 33 DBS samples were sent to us today from Mibenge Clinic. We will notify you when the results are ready.
        """

    testReportResultsCorrection = """
            clinic_worker > SENT twenti two
            clinic_worker < Hello John Banda! We received your notification that 22 DBS samples were sent to us today from Mibenge Clinic. We will notify you when the results are ready.
        """

    testReportRemovalOfExtraWords = """
            clinic_worker > SENT 40 samples anythin
            clinic_worker < Hello John Banda! We received your notification that 40 DBS samples were sent to us today from Mibenge Clinic. We will notify you when the results are ready.
        """
        
    testZeroSampleNumber = """
            clinic_worker > SENT 0
            clinic_worker < Sorry, the number of DBS samples sent must be greater than 0 (zero).
        """
    testNegativeSampleNumber = """
            clinic_worker > SENT -1
            clinic_worker < Sorry, the number of DBS samples sent must be greater than 0 (zero).
        """

    testBadReportFormat = """
            clinic_worker > SENT some samples yo!
            clinic_worker < Sorry, we didn't understand that message. To report DBS samples sent, send SENT <NUMBER OF SAMPLES>
        """
        
    testUnregisteredResults = """
            unknown_user > SENT 3
            unknown_user < Sorry, you must be registered with Results160 to report DBS samples sent. If you think this message is a mistake, respond with keyword 'HELP'
        """
        
    testUnregisteredCheck = """
            unknown_user > CHECK RESULTS
            unknown_user < Sorry you must be registered with a clinic to check results. To register, send JOIN <CLINIC CODE> <NAME> <SECURITY CODE>
        """
        
    testCheckResultsNone = """
            clinic_worker > CHECK RESULTS
            clinic_worker < Hello John Banda. There are no new DBS test results for Mibenge Clinic right now. We'll let you know as soon as more results are available.
    """
    
    def testSentCreatesDbObjects(self):
        self.assertEqual(0, SampleNotification.objects.count())
        script = """
            clinic_worker > SENT 5
            clinic_worker < Hello John Banda! We received your notification that 5 DBS samples were sent to us today from Mibenge Clinic. We will notify you when the results are ready.
        """
        self.runScript(script)
        self.assertEqual(1, SampleNotification.objects.count())
        notification = SampleNotification.objects.all()[0]
        self.assertEqual(5, notification.count)
        self.assertEqual(self.clinic, notification.location)
        self.assertEqual(self.contact, notification.contact)
        
    def testResultsPIN(self):
        # NOTE: this test is failing and I'm not sure why.
        # It works fine in the message tester.
        
        res1, res2, res3 = self._bootstrap_results()
        # initiate a test and before sending a correct PIN try a bunch 
        # of different things.
        # some messages should trigger a PIN wrong answer, others shouldn't
        use_many_messages = False
        res1furtherdetails = res1.sample_id
        if res1.result is None:
            res1display = 'Not Yet Tested'
        else:
            res1display = res1.get_result_display()
            if res1.result.upper() in 'IXR':
                res1furtherdetails = res1.sample_id + ', ' + res1.result_detail
                res1display = 'Not Ready'
                use_many_messages = True

        res2furtherdetails = res2.sample_id
        if res2.result is None:
            res2display = 'Not Yet Tested'
        else:
            res2display = res2.get_result_display()
            if res2.result.upper() in 'IXR':
                res2furtherdetails = res2.sample_id + ', ' + res2.result_detail
                res2display = 'Not Ready'
                use_many_messages = True

        res3furtherdetails = res3.sample_id
        if res3.result is None or len(res3.result.strip()) == 0:
            res3display = 'Not Yet Tested'
        else:
            res3display = res3.get_result_display()
            if res3.result.upper() in 'IXR':
                res3furtherdetails = res3.sample_id + ', ' + res3.result_detail
                res3display = 'Not Ready'
                use_many_messages = True
        script = """
            clinic_worker > CHECK RESULTS
            clinic_worker < Hello %(name)s. We have %(count)s DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results.
            clinic_worker > 55555
            clinic_worker < Sorry, that was not the correct security code. Your security code is a 4-digit number like 1234. If you forgot your security code, reply with keyword 'HELP'
            clinic_worker > Help
            clinic_worker < Sorry you're having trouble %(name)s. Your help request has been forwarded to a support team member and they will call you soon.
            clinic_worker > RESULT 12345
            clinic_worker < Sorry, no sample with id 12345 was found for your clinic. Please check your DBS records and try again.
            clinic_worker > CHECK RESULTS
            clinic_worker < Hello %(name)s. We have %(count)s DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results.
            clinic_worker > here's some stuff that you won't understand
            clinic_worker < Sorry, that was not the correct security code. Your security code is a 4-digit number like 1234. If you forgot your security code, reply with keyword 'HELP'
            clinic_worker > %(code)s
            """% {"name": self.contact.name, "count": 3, "code": "4567"}
        self.runScript(script)

        if use_many_messages:
            script="""
                clinic_worker < Thank you! Here are your results: Sample %(id1)s: %(res1)s, Lab ID = %(det1)s. Sample %(id2)s: %(res2)s, Lab ID = %(det2)s
                clinic_worker < Sample %(id3)s: %(res3)s, Lab ID = %(det3)s
                clinic_worker < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again %(name)s!
            """ % {"name": self.contact.name, "count": 3, "code": "4567",
                "id1": res1.requisition_id, "res1": res1display, "det1": res1furtherdetails,
                "id2": res2.requisition_id, "res2": res2display, "det2": res2furtherdetails,
                "id3": res3.requisition_id, "res3": res3display, "det3": res3furtherdetails}
        
        else:
            script="""
                clinic_worker < Thank you! Here are your results: Sample %(id1)s: %(res1)s, Lab ID = %(det1)s. Sample %(id2)s: %(res2)s, Lab ID = %(det2)s. Sample %(id3)s: %(res3)s, Lab ID = %(det3)s
                clinic_worker < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again %(name)s!
            """ % {"name": self.contact.name, "count": 3, "code": "4567",
                "id1": res1.requisition_id, "res1": res1display, "det1": res1furtherdetails,
                "id2": res2.requisition_id, "res2": res2display, "det2": res2furtherdetails,
                "id3": res3.requisition_id, "res3": res3display, "det3": res3furtherdetails}
        self.runScript(script)
        
        
    def testCheckResultsWorkflow(self):
        """Tests the "check" functionality"""
        
        # Save some results
        res1, res2, res3 = self._bootstrap_results()
        
        # These would be automatically sent by a scheduled task, but we
        # also support querying them via these magic keywords
        script = """
            clinic_worker > CHECK RESULTS
            clinic_worker < Hello %(name)s. We have %(count)s DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results.
        """ % {"name": self.contact.name, "count": 3}
        self.runScript(script)
        
        for res in [labresults.Result.objects.get(id=res.id)
                    for res in [res1, res2, res3]]:
            self.assertEqual("notified", res.notification_status)

        use_many_messages = False
        res1furtherdetails = res1.sample_id
        if res1.result is None:
            res1display = 'Not Yet Tested'
        else:
            res1display = res1.get_result_display()
            if res1.result.upper() in 'IXR':
                res1furtherdetails = res1.sample_id + ', ' + res1.result_detail
                res1display = 'Not Ready'
                use_many_messages = True

        res2furtherdetails = res2.sample_id
        if res2.result is None:
            res2display = 'Not Yet Tested'
        else:
            res2display = res2.get_result_display()
            if res2.result.upper() in 'IXR':
                res2furtherdetails = res2.sample_id + ', ' + res2.result_detail
                res2display = 'Not Ready'
                use_many_messages = True

        res3furtherdetails = res3.sample_id
        if res3.result is None or len(res3.result.strip()) == 0:
            res3display = 'Not Yet Tested'            
        else:
            res3display = res3.get_result_display()
            if res3.result.upper() in 'IXR':
                res3furtherdetails = res3.sample_id + ', ' + res3.result_detail
                res3display = 'Not Ready'
                use_many_messages = True

        if  use_many_messages:
            script = """
                clinic_worker > %(code)s
                clinic_worker < Thank you! Here are your results: Sample %(id1)s: %(res1)s, Lab ID = %(det1)s. Sample %(id2)s: %(res2)s, Lab ID = %(det2)s
                clinic_worker < Sample %(id3)s: %(res3)s, Lab ID = %(det3)s
                clinic_worker < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again %(name)s!
            """ % {"name": self.contact.name, "code": "4567",
                "id1": res1.requisition_id, "res1": res1display, "det1": res1furtherdetails,
                "id2": res2.requisition_id, "res2": res2display, "det2": res2furtherdetails,
                "id3": res3.requisition_id, "res3": res3display, "det3": res3furtherdetails}
        else:
            script = """
                clinic_worker > %(code)s
                clinic_worker < Thank you! Here are your results: Sample %(id1)s: %(res1)s, Lab ID = %(det1)s. Sample %(id2)s: %(res2)s, Lab ID = %(det2)s. Sample %(id3)s: %(res3)s, Lab ID = %(det3)s
                clinic_worker < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again %(name)s!
            """ % {"name": self.contact.name, "code": "4567",
                "id1": res1.requisition_id, "res1": res1display, "det1": res1furtherdetails,
                "id2": res2.requisition_id, "res2": res2display, "det2": res2furtherdetails,
                "id3": res3.requisition_id, "res3": res3display, "det3": res3furtherdetails}
#        # TODO : find solution form this
#        print ""
#        print "*" * 75
#        print "This test will fail if all the 'random' results fit within 160 ",
#        print "characters, otherwise we expect them to fit in two messages"
        self.runScript(script)
        
        for res in [labresults.Result.objects.get(id=res.id)
                    for res in [res1, res2, res3]]:
            self.assertEqual("sent", res.notification_status)
    
    def testDemoResultsWorkflow(self):
        """
        Tests demo results delivery mechanism.
        """
        self.assertEqual(0, Result.objects.count())
        
        # because we don't know what dummy result will be generated, and because
        # we aren't certain how ordering works, we have to do this test 
        # manually via the router apis
        self.startRouter()
        try:
            # do this whole thing a few times, so we know it can be demoed back
            # to back and also test the format of specifying an explicit clinic
            # code
            for start_msg_spec in (("clinic_worker", "DEMO"), 
                                   ("other_worker", "DEMO RESULTS"),
                                   ("some_random_person", "DEMO mib")):
                self.sendMessage(*start_msg_spec)
                messages = self.receiveAllMessages()
                self.assertEqual(2, len(messages), "Number of messages didn't match. "
                                 "Messages back were: %s" % messages)
                for msg in messages:
                    self.assertTrue(msg.connection.identity in ["clinic_worker", "other_worker"])
                    self.assertEqual("Hello %(name)s. We have 3 DBS test results ready for you. "
                                     "Please reply to this SMS with your security code to retrieve "
                                     "these results." % {"name": msg.contact.name}, msg.text)
                                     
                
                self.assertEqual(0, Result.objects.count())
                
                self.sendMessage("clinic_worker", "4567")
                messages = self.receiveAllMessages()
                #TODO: length may be equal to 3 if the random messages cab all fit in 160 chars
#                length = 4
#                self.assertEqual(length, len(messages), "Number of messages didn't match. "
#                                 "Messages back were: %s" % messages)
                for msg in messages:
                    if msg.text.startswith("John"):
                        self.assertEqual("other_worker", msg.connection.identity)
                        self.assertEqual("John Banda has collected these results", msg.text)
                    elif msg.text.startswith("Thank you! Here are your results: "):
                        self.assertEqual("clinic_worker", msg.connection.identity)
                    elif msg.text.startswith("Please"):
                        self.assertEqual("clinic_worker", msg.connection.identity)
                        self.assertEqual("Please record these results in your clinic "
                                         "records and promptly delete them from your "
                                         "phone.  Thank you again John Banda!",
                                         msg.text)
                    elif "Not Yet Tested" not in msg.text:
                        self.fail("Unexpected response to pin: %s" % msg.text)
                
                # we still should have no results in the db
                self.assertEqual(0, Result.objects.count())
            
        finally:
            self.stopRouter()
    
    def _bootstrap_results(self):
        results = get_fake_results(3, self.clinic, notification_status_choices=("new", ))
        for res in results:  res.save()
        return results
    
    def testResultsSample(self):
        """
        Tests getting of results for given samples.
        """
        results = labresults.Result.objects.all()
        res1 = results.create(requisition_id="0001", clinic=self.clinic,
                              result="N",
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new",
                              sample_id = "lb01")

        res2 = results.create(requisition_id="0002", clinic=self.clinic,
                              result="P",
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new",
                              sample_id = "lb02")

        res3 = results.create(requisition_id="0003", clinic=self.clinic,
                              result="R",
                              result_detail="contaminated",
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new",
                              sample_id="lb03")

        res4 = results.create(requisition_id="0004", clinic=self.clinic,
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new",
                              sample_id = "lb04")

        res4a = results.create(requisition_id="0004a", clinic=self.clinic,
                               collected_on=datetime.datetime.today(),
                               entered_on=datetime.datetime.today(),
                               notification_status="new",
                              sample_id = "lb04a")

        res4b = results.create(requisition_id="0004b", clinic=self.clinic,
                               collected_on=datetime.datetime.today(),
                               entered_on=datetime.datetime.today(),
                               notification_status="new",
                              sample_id = "lb04b")

        res5 = results.create(requisition_id="0000", clinic=self.clinic,
                              result="R",
                              result_detail="machine is down",
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new",
                              sample_id = "lb00")

        res6 = results.create(requisition_id="0000", clinic=self.clinic,
                              result="P",
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new",
                              sample_id = "lb00")
        
        script = """
            clinic_worker > RESULT 000 1
            clinic_worker < Sorry, no samples with ids 000, 1 were found for your clinic. Please check your DBS records and try again.
            clinic_worker > RESULT 0003
            clinic_worker < Results not ready, 0003: Rejected Sample, Lab ID = lb03, contaminated
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone. Thank you again.
            clinic_worker > RESULT 0004
            clinic_worker < Results not ready, 0004: Not Yet Tested, Lab ID = lb04
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone. Thank you again.
            clinic_worker > RESULT 0004a 0004b
            clinic_worker < Results not ready, 0004a: Not Yet Tested, Lab ID = lb04a; 0004b: Not Yet Tested, Lab ID = lb04b
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone. Thank you again.
            clinic_worker > RESULT 0004a,0004b
            clinic_worker < Results not ready, 0004a: Not Yet Tested, Lab ID = lb04a; 0004b: Not Yet Tested, Lab ID = lb04b
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone. Thank you again.
            clinic_worker > RESULT 0004a,0003
            clinic_worker < Results not ready, 0004a: Not Yet Tested, Lab ID = lb04a; 0003: Rejected Sample, Lab ID = lb03, contaminated
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone. Thank you again.
            clinic_worker > RESULT 6006
            clinic_worker < Sorry, no sample with id 6006 was found for your clinic. Please check your DBS records and try again.
            clinic_worker > RESULT 0001
            clinic_worker < 0001: Not Detected, Lab ID = lb01
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone. Thank you again.
            clinic_worker > RESULT 0002
            clinic_worker < 0002: Detected, Lab ID = lb02
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone. Thank you again.
            clinic_worker > RESULT 0000
            clinic_worker < 0000: Detected, Lab ID = lb00
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone. Thank you again.
            clinic_worker < Results not ready, 0000: Rejected Sample, Lab ID = lb00, machine is down
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone. Thank you again.
            unkown_worker > RESULT 0000
            unkown_worker < Sorry, you must be registered with Results160 to report DBS samples sent. If you think this message is a mistake, respond with keyword 'HELP'
           """

        self.runScript(script)

        for res in [results.get(id=res.id) for res in [res1, res2, res3, res5, res6]]:
            self.assertEqual("sent", res.notification_status)
        self.assertEqual("new", res4.notification_status)


class ResultsAcceptor(TestScript):
    apps = (handler_app, App)
    
    def _post_json(self, url, data):
        return self.client.post(url, json.dumps(data),
                                content_type='text/json')
    
    def test_payload_entry(self):
        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='labresults',
                                      codename='add_payload')
        user.user_permissions.add(perm)
        self.client.login(username='adh', password='abc')
        data = {'varname': 'data'}
        now = datetime.datetime.now()
        response = self._post_json(reverse('accept_results'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(labresults.Payload.objects.count(), 1)
        payload = labresults.Payload.objects.get()
        self.assertEqual(payload.raw, json.dumps(data))
        self.assertTrue(payload.parsed_json)
        self.assertFalse(payload.validated_schema)
        self.assertEqual(user, payload.auth_user)
        self.assertEqual(payload.incoming_date.year, now.year)
        self.assertEqual(payload.incoming_date.month, now.month)
        self.assertEqual(payload.incoming_date.day, now.day)
        self.assertEqual(payload.incoming_date.hour, now.hour)
    
    def test_payload_login_required(self):
        data = {'varname': 'data'}
        response = self._post_json(reverse('accept_results'), data)
        self.assertEqual(response.status_code, 401) # authorization required
        self.assertEqual(labresults.Payload.objects.count(), 0)
    
    def test_payload_permission_required(self):
        User.objects.create_user(username='adh', email='', password='abc')
        self.client.login(username='adh', password='abc')
        data = {'varname': 'data'}
        response = self._post_json(reverse('accept_results'), data)
        self.assertEqual(response.status_code, 401) # authorization required
        self.assertEqual(labresults.Payload.objects.count(), 0)
    
    def test_payload_post_required(self):
        response = self.client.get(reverse('accept_results'))
        self.assertEqual(response.status_code, 405) # method not supported
