import json

from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse

from mwana.apps.labresults import models as labresults

from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.contrib.locations.models import LocationType, Location
from rapidsms.models import Contact, Connection
from rapidsms.tests.scripted import TestScript
from mwana.apps.labresults.app import App
import datetime

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
                                              location=self.clinic, pin="4567", 
                                              is_results_receiver=True)
        connection.contact = self.contact
        connection.save()
        
        # create another one
        self.other_contact = Contact.objects.create(alias="mary", name="Mary Phiri", 
                                                    location=self.clinic, pin="6789", 
                                                    is_results_receiver=True)
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
        self.assertEqual(True, contact.is_results_receiver)
    
    testReportResults = """
            clinic_worker > SENT 3
            clinic_worker < Hello John Banda! We received your notification that 3 DBS samples were sent to us today from Mibenge Clinic. We will notify you when the results are ready.
            
        """
        
    testBadReportFormat = """
            clinic_worker > SENT some samples yo!
            clinic_worker < Sorry, we didn't understand that message. To report DBS samples sent, send SENT <NUMBER OF SAMPLES>
        """
        
    testUnregisteredResults = """
            unknown_user > SENT 3
            unknown_user < Sorry, you must be registered with Results160 to report DBS samples sent. If you think this message is a mistake, respond with keyword 'HELP'
        """
        
    def testResultsWorkflow(self):
        """
        Tests basic results delivery mechanism.
        """
        # Due to the intensive overhead of creating all these objects this is
        # much more of an integration test than a unit test.
        # Save some results
        res1 = labresults.Result.objects.create(sample_id="0001", clinic=self.clinic, 
                                     result="N", 
                                     taken_on=datetime.datetime.today(),
                                     entered_on=datetime.datetime.today(), 
                                     notification_status="new")
        
        res2 = labresults.Result.objects.create(sample_id="0002", clinic=self.clinic, result="P", 
                              taken_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(), 
                              notification_status="new")
        
        res3 = labresults.Result.objects.create(sample_id="0003", clinic=self.clinic, result="N", 
                              taken_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(), 
                              notification_status="new")

        # These would be automatically sent by a scheduled task, but we
        # also support querying them via these magic keywords
        script = """
            clinic_worker > CHECK RESULTS
            clinic_worker < Hello %(name)s. We have %(count)s DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results.
            other_worker  < Hello %(other_name)s. We have %(count)s DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results.
        """ % {"name": self.contact.name, "other_name": self.other_contact.name, "count": 3 }
        self.runScript(script)
        
        for res in [labresults.Result.objects.get(id=res.id) for res in [res1, res2, res3]]:
            self.assertEqual("notified", res.notification_status)
        
        script = """
            clinic_worker > %(code)s
            # because of rapidsms LIFO responses, this one makes its way through the 
            # router first.  
            other_worker  < John Banda has collected these results
            clinic_worker < Thank you! Here are your results: Sample 0001: HIV Negative, Sample 0002: HIV Positive, Sample 0003: HIV Negative
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again %(name)s!
        """ % {"name": self.contact.name, "code": "4567", }
        
        self.runScript(script)
        
        for res in [labresults.Result.objects.get(id=res.id) for res in [res1, res2, res3]]:
            self.assertEqual("sent", res.notification_status)
            
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
            clinic_worker < The sample id must not have spaces in between. To request for results for a DBS sample, send RESULT <sampleid>. E.g result ID45
            clinic_worker > RESULT 0004
            clinic_worker < The results for sample 0004 are not yet ready. You will be notified when they are ready.
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



        
