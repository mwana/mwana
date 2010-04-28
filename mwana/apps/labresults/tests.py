from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from mwana.apps.labresults import models as labresults
from mwana.apps.labresults.app import App
from mwana.apps.labresults.models import Result
from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.contrib.locations.models import LocationType, Location
from rapidsms.models import Contact, Connection
from rapidsms.tests.scripted import TestScript
import datetime
import json
from mwana.apps.labresults.mocking import get_fake_results
import mwana.const as const



class TestApp(TestScript):
    apps = (handler_app, App)
    
    def setUp(self):
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
            clinic_worker < Hello John Banda. There are no new DBS test results for Mibenge Clinic right now. We'll let you as soon as more results are available.
    """
    
    def testResultsPIN(self):
        # NOTE: this test is failing and I'm not sure why.
        # It works fine in the message tester.
        
        res1, res2, res3 = self._bootstrap_results()
        # initiate a test and before sending a correct PIN try a bunch 
        # of different things.
        # some messages should trigger a PIN wrong answer, others shouldn't
        script = """
            clinic_worker > CHECK RESULTS
            clinic_worker < Hello %(name)s. We have %(count)s DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results.
            clinic_worker > 5555
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
            clinic_worker < Thank you! Here are your results: Sample %(id1)s: %(res1)s. Sample %(id2)s: %(res2)s. Sample %(id3)s: %(res3)s
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again %(name)s!
        """ % {"name": self.contact.name, "count": 3, "code": "4567", 
               "id1": res1.sample_id, "res1": res1.get_result_display(),
               "id2": res2.sample_id, "res2": res2.get_result_display(),
               "id3": res3.sample_id, "res3": res3.get_result_display()} 
        
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
        """ % {"name": self.contact.name, "count": 3 }
        self.runScript(script)
        
        for res in [labresults.Result.objects.get(id=res.id) for res in [res1, res2, res3]]:
            self.assertEqual("notified", res.notification_status)
        
        script = """
            clinic_worker > %(code)s
            clinic_worker < Thank you! Here are your results: Sample %(id1)s: %(res1)s. Sample %(id2)s: %(res2)s. Sample %(id3)s: %(res3)s
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again %(name)s!
        """ % {"name": self.contact.name, "code": "4567", 
               "id1": res1.sample_id, "res1": res1.get_result_display(),
               "id2": res2.sample_id, "res2": res2.get_result_display(),
               "id3": res3.sample_id, "res3": res3.get_result_display()}
                
        self.runScript(script)
        
        for res in [labresults.Result.objects.get(id=res.id) for res in [res1, res2, res3]]:
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
                self.assertEqual(3, len(messages), "Number of messages didn't match. "
                                 "Messages back were: %s" % messages)
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
                    else:
                        self.fail("Unexpected response to pin: %s" % msg.text)
                
                # we still should have no results in the db
                self.assertEqual(0, Result.objects.count())
            
        finally:
            self.stopRouter()
    
    def _bootstrap_results(self):
        results = get_fake_results(3, self.clinic, notification_status_choices=("new",))
        for res in results:  res.save()
        return results
        
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

    def testResultsSample(self):
        """
        Tests getting of results for given samples.
        """
        res1 = labresults.Result.objects.create(sample_id="0001", clinic=self.clinic,
                                     result="N",
                                     taken_on=datetime.datetime.today(),
                                     entered_on=datetime.datetime.today(),
                                     notification_status="new")

        res2 = labresults.Result.objects.create(sample_id="0002", clinic=self.clinic, result="P",
                              taken_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")

        res3 = labresults.Result.objects.create(sample_id="0003", clinic=self.clinic, result="B",
                              taken_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")

        res4 = labresults.Result.objects.create(sample_id="0004", clinic=self.clinic,
                              taken_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")

        res4b = labresults.Result.objects.create(sample_id="0004b", clinic=self.clinic,
                              taken_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")

        res5 = labresults.Result.objects.create(sample_id="0000", clinic=self.clinic, result="B",
                              taken_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")

        res6 = labresults.Result.objects.create(sample_id="0000", clinic=self.clinic, result="P",
                              taken_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")



        script = """
            clinic_worker > RESULT 000 1
            clinic_worker < Sorry, no samples with ids 000, 1 were found for your clinic. Please check your DBS records and try again.
            clinic_worker > RESULT 0004
            clinic_worker < The results for sample(s) 0004 are not yet ready. You will be notified when they are ready.
            clinic_worker > RESULT 0004,0004b
            clinic_worker < The results for sample(s) 0004, 0004b are not yet ready. You will be notified when they are ready.
            clinic_worker > RESULT 6006
            clinic_worker < Sorry, no sample with id 6006 was found for your clinic. Please check your DBS records and try again.
            clinic_worker > RESULT 0001
            clinic_worker < 0001: HIV Negative
            clinic_worker > RESULT 0002
            clinic_worker < 0002: HIV Positive
            clinic_worker > RESULT 0003
            clinic_worker < 0003: Bad Sample
            clinic_worker > RESULT 0000
            clinic_worker < 0000: Bad Sample, 0000: HIV Positive
            unkown_worker > RESULT 0000
            unkown_worker < Sorry, you must be registered with Results160 to report DBS samples sent. If you think this message is a mistake, respond with keyword 'HELP'
           """

        self.runScript(script)


        for res in [labresults.Result.objects.get(id=res.id) for res in [res1, res2, res3, res5, res6]]:
            self.assertEqual("sent", res.notification_status)
        self.assertEqual("new", res4.notification_status)
