from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.contrib.locations.models import LocationType, Location
from rapidsms.models import Contact, Connection
from rapidsms.tests.scripted import TestScript
from mwana.apps.labresults.app import App
from mwana.apps.labresults.models import Result
import datetime

class TestApp(TestScript):
    apps = (handler_app, App)
    
    def setUp(self):
        super(TestApp, self).setUp()
        self.type = LocationType.objects.create(singular="clinic", plural="clinics", slug="clinics")
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
        
    def testResults(self):
        """
        Tests basic results delivery mechanism.
        """
        # Due to the intensive overhead of creating all these objects this is
        # much more of an integration test than a unit test.
        # Save some results
        res1 = Result.objects.create(sample_id="0001", clinic=self.clinic, 
                                     result="N", 
                                     taken_on=datetime.datetime.today(),
                                     entered_on=datetime.datetime.today(), 
                                     notification_status="new")
        
        res2 = Result.objects.create(sample_id="0002", clinic=self.clinic, result="P", 
                              taken_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(), 
                              notification_status="new")
        
        res3 = Result.objects.create(sample_id="0003", clinic=self.clinic, result="N", 
                              taken_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(), 
                              notification_status="new")

        # These would be automatically sent by a scheduled task, but we
        # also support querying them via these magic keywords
        script = """
            clinic_worker > CHECK RESULTS
            clinic_worker < Hello %(name)s. We have %(count)s DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results.
        """ % {"name": self.contact.name, "count": 3 }
        self.runScript(script)
        
        for res in [Result.objects.get(id=res.id) for res in [res1, res2, res3]]:
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
        
        for res in [Result.objects.get(id=res.id) for res in [res1, res2, res3]]:
            self.assertEqual("sent", res.notification_status)
            
        