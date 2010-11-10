import time
import json

import datetime
import mwana.const as const
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from mwana.apps.labresults import models as labresults
from mwana.apps.labresults.mocking import get_fake_results
from mwana.apps.labresults.models import Result, SampleNotification
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from rapidsms.models import Connection
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from mwana.apps.labresults import tasks
from mwana.util import is_today_a_weekend, is_weekend
from mwana.apps.labresults.testdata.payloads import INITIAL_PAYLOAD, CHANGED_PAYLOAD
from mwana.apps.labresults.testdata.reports import *


class LabresultsSetUp(TestScript):
    
    def setUp(self):
        # this call is required if you want to override setUp
        super(LabresultsSetUp, self).setUp()
        self.type = LocationType.objects.get_or_create(singular="clinic", plural="clinics", slug=const.CLINIC_SLUGS[2])[0]
        self.type1 = LocationType.objects.get_or_create(singular="district", plural="districts", slug="districts")[0]        
        self.type2 = LocationType.objects.get_or_create(singular="province", plural="provinces", slug="provinces")[0]        
        self.luapula = Location.objects.create(type=self.type2, name="Luapula Province", slug="luapula")
        self.mansa = Location.objects.create(type=self.type1, name="Mansa District", slug="mansa", parent = self.luapula)
        self.samfya = Location.objects.create(type=self.type1, name="Samfya District", slug="samfya", parent = self.luapula)
        self.clinic = Location.objects.create(type=self.type, name="Mibenge Clinic", slug="402029", parent = self.samfya)
        self.mansa_central = Location.objects.create(type=self.type, name="Central Clinic", slug="403012", parent = self.mansa)

        
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
        super(LabresultsSetUp, self).tearDown()
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

class TestApp(LabresultsSetUp):
    testReportResults = """
            clinic_worker > SENT 33
            clinic_worker < Hello John Banda! We received your notification that 33 DBS samples were sent to us today from Mibenge Clinic. We will notify you when the results are ready.
        """

    testReportResultsCorrection = """
            clinic_worker > snt hundred twenti 5 samples
            clinic_worker < Hello John Banda! We received your notification that 125 DBS samples were sent to us today from Mibenge Clinic. We will notify you when the results are ready.
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
            clinic_worker < Hello John Banda! We received your notification that 1 DBS samples were sent to us today from Mibenge Clinic. We will notify you when the results are ready.
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
    
    # TODO: flesh out this test
    """
        524754 > join 402010 cory 1234
        524754 < Your phone is already registered to Tba at 1. To change name or clinic first reply with keyword 'LEAVE' and try again.
        524754 > join 401010 cory 1234
        524754 < Hi Cory, thanks for registering for DBS results from Results160 as staff of Chipungu. Your PIN is 1234. Reply with keyword 'HELP' if your information is not correct.
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
        script = """
            clinic_worker > CHECK RESULTS
            clinic_worker < Hello %(name)s. We have %(count)s DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results.
            clinic_worker > 55555
            clinic_worker < Sorry, that was not the correct security code. Your security code is a 4-digit number like 1234. If you forgot your security code, reply with keyword 'HELP'
            clinic_worker > Help
            support_contact < John Banda at Mibenge Clinic has requested help. Please call them at clinic_worker as soon as you can!
            support_contact2 < John Banda at Mibenge Clinic has requested help. Please call them at clinic_worker as soon as you can!
            clinic_worker < Sorry you're having trouble %(name)s. Your help request has been forwarded to a support team member and they will call you soon.
            clinic_worker > RESULT 12345
            clinic_worker < There are currently no results available for 12345. Please check if the SampleID is correct or sms HELP if you have been waiting for 2 months or more
            clinic_worker > CHECK RESULTS
            clinic_worker < Hello %(name)s. We have %(count)s DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results.
            clinic_worker > here's some stuff that you won't understand
            clinic_worker < Sorry, that was not the correct security code. Your security code is a 4-digit number like 1234. If you forgot your security code, reply with keyword 'HELP'
            clinic_worker > %(code)s
            clinic_worker < Thank you! Here are your results: **** %(id1)s;%(res1)s. **** %(id2)s;%(res2)s. **** %(id3)s;%(res3)s
                clinic_worker < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again %(name)s!
            """ % {"name": self.contact.name, "count": 3, "code": "4567",
            "id1": res1.requisition_id, "res1": res1.get_result_display(),
            "id2": res2.requisition_id, "res2": res2.get_result_display(),
            "id3": res3.requisition_id, "res3": res3.get_result_display()}
        
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

            script = """
                clinic_worker > %(code)s
            clinic_worker < Thank you! Here are your results: **** %(id1)s;%(res1)s. **** %(id2)s;%(res2)s. **** %(id3)s;%(res3)s
                clinic_worker < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again %(name)s!
            """ % {"name": self.contact.name, "code": "4567",
            "id1": res1.requisition_id, "res1": res1.get_result_display(),
            "id2": res2.requisition_id, "res2": res2.get_result_display(),
            "id3": res3.requisition_id, "res3": res3.get_result_display()}

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
                                   ("some_random_person", "DEMO 402029")):
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
                              notification_status="new")

        res2 = results.create(requisition_id="0002", clinic=self.clinic,
                              result="P",
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")

        res3 = results.create(requisition_id="0003", clinic=self.clinic,
                              result="N",
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")

        res4 = results.create(requisition_id="0004", clinic=self.clinic,
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")

        res4a = results.create(requisition_id="0004a", clinic=self.clinic,
                               collected_on=datetime.datetime.today(),
                               entered_on=datetime.datetime.today(),
                               notification_status="new")

        res4b = results.create(requisition_id="0004b", clinic=self.clinic,
                               collected_on=datetime.datetime.today(),
                               entered_on=datetime.datetime.today(),
                               notification_status="new")

#        res5 = results.create(requisition_id="0000", clinic=self.clinic,
#                              result="R",
#                              collected_on=datetime.datetime.today(),
#                              entered_on=datetime.datetime.today(),
#                              notification_status="new")

        res6 = results.create(requisition_id="0000", clinic=self.clinic,
                              result="P",
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")
        
        script = """
            clinic_worker > RESULT 9999
            clinic_worker < Sample 9999: Detected. Please record these results in your clinic records and promptly delete them from your phone. Thanks again
            clinic_worker > RESULT 000 1
            clinic_worker < There are currently no results available for 1, 000. Please check if the SampleID's are correct or sms HELP if you have been waiting for 2 months or more
            clinic_worker > RESULT 0004
            clinic_worker < The results for sample(s) 0004 are not yet ready. You will be notified when they are ready.
            clinic_worker > RESULT 0004a 0004b
            clinic_worker < The results for sample(s) 0004a, 0004b are not yet ready. You will be notified when they are ready.
            clinic_worker > RESULT 0004a , 0004b
            clinic_worker < The results for sample(s) 0004a, 0004b are not yet ready. You will be notified when they are ready.
            clinic_worker > RESULT 6006
            clinic_worker < There are currently no results available for 6006. Please check if the SampleID is correct or sms HELP if you have been waiting for 2 months or more
            clinic_worker > RESULT 0001
            clinic_worker < **** 0001;NotDetected. Please record these results in your clinic records and promptly delete them from your phone. Thanks again
            clinic_worker > RESULT 0003
            clinic_worker < **** 0003;NotDetected. Please record these results in your clinic records and promptly delete them from your phone. Thanks again
            clinic_worker > RESULT 0002
            clinic_worker < **** 0002;Detected. Please record these results in your clinic records and promptly delete them from your phone. Thanks again
            clinic_worker > RESULT 0000
            clinic_worker < **** 0000;Detected. Please record these results in your clinic records and promptly delete them from your phone. Thanks again
            clinic_worker > RESULT 0001 0002
            clinic_worker < **** 0001;NotDetected. **** 0002;Detected. Please record these results in your clinic records and promptly delete them from your phone. Thanks again
            unkown_worker > RESULT 0000
            unkown_worker < Sorry, you must be registered with Results160 to receive DBS results. If you think this message is a mistake, respond with keyword 'HELP'
           """

        self.runScript(script)

        for res in [results.get(id=res.id) for res in [res1, res2, res3]]:
            self.assertEqual("sent", res.notification_status)
        self.assertEqual("new", res4.notification_status)

    def testReports(self):
        """
        Tests getting of report for sent results. A report for a district
        aggregates counts from the facilities it has. Same applies to a Province
        """
        # create 7 results. 5 for Mibenge in Samfya district of Luapula province
        #, 2 for Central Clinic of Mansa district in Luapula Provice
        results = labresults.Result.objects.all()
        res1 = results.create(requisition_id="0001", clinic=self.clinic,
                              result="N",
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")

        res2 = results.create(requisition_id="0002", clinic=self.clinic,
                              result="P",
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")

        res3 = results.create(requisition_id="0003", clinic=self.clinic,
                              result="N",
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")

        res4 = results.create(requisition_id="0004", clinic=self.clinic,
                              result="N",
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")

        res5 = results.create(requisition_id="0004a", clinic=self.clinic,
                               result="R",
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")

        res6 = results.create(requisition_id="0004b", clinic=self.mansa_central,
                               result="N",
                               collected_on=datetime.datetime.today(),
                               entered_on=datetime.datetime.today(),
                               notification_status="new")


        res7 = results.create(requisition_id="0000", clinic=self.mansa_central,
                              result="P",
                              collected_on=datetime.datetime.today(),
                              entered_on=datetime.datetime.today(),
                              notification_status="new")
        
        #collect the results. get some reports
        script = """
            central_clinic_worker > CHECK
            central_clinic_worker < Hello James Phiri. We have 2 DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results.
            central_clinic_worker > 1111
            central_clinic_worker < Thank you! Here are your results: **** 0000;Detected. **** 0004b;NotDetected
            central_clinic_worker < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again James Phiri!
            clinic_worker > CHECK
            clinic_worker < Hello John Banda. We have 5 DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results.
            clinic_worker > 4567
            clinic_worker < Thank you! Here are your results: **** 0001;NotDetected. **** 0002;Detected. **** 0003;NotDetected. **** 0004;NotDetected. **** 0004a;Rejected
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again John Banda!
            clinic_worker > Reports
            clinic_worker < To view a report, send REPORT <CLINIC_CODE> [MONTH]
            clinic_worker > Reports 403029
            clinic_worker < Sorry, I don't know about a location with code 403029. Please check your code and try again.
            clinic_worker > Reports 402029
            clinic_worker > Reports 403012
            clinic_worker > Reports 403012 Nov
            clinic_worker > Reports 403012 11
            clinic_worker > Reports 402000
            clinic_worker > Reports 403000
            clinic_worker > Reports 4030
            clinic_worker > Reports mansa
            clinic_worker > Reports 400000
            clinic_worker > Reports 40 Nov
            clinic_worker > Reports Luapula
        """
        self.runScript(script)        
        msgs=self.receiveAllMessages()
        
        #test that the correct reports were received
        self.assertEqual(msgs[len(msgs)-1].text,province_report2)
        self.assertEqual(msgs[len(msgs)-2].text,province_report1)#month dependent
        self.assertEqual(msgs[len(msgs)-3].text,province_report1)
        self.assertEqual(msgs[len(msgs)-4].text,mansa_report1)
        self.assertEqual(msgs[len(msgs)-5].text,mansa_report1)
        self.assertEqual(msgs[len(msgs)-6].text,mansa_report1)
        self.assertEqual(msgs[len(msgs)-7].text,samfya_report1)
        self.assertEqual(msgs[len(msgs)-8].text,central_clinc_rpt)
        self.assertEqual(msgs[len(msgs)-9].text,central_clinc_rpt)
        self.assertEqual(msgs[len(msgs)-10].text,central_clinc_rpt)
        self.assertEqual(msgs[len(msgs)-11].text,mibenge_report1)
        

class TestResultsAcceptor(LabresultsSetUp):
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

    def test_payload_complex_entry(self):
        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='labresults',
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
                    "child_age_unit": "weeks",
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
                    "child_age_unit": "weeks",
                    "verified": True
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
                    "pat_id": "21234987", 
                    "dob": "2010-01-12", 
                    "proc_on": "2010-04-17", 
                    "child_age": 4,
                    "child_age_unit": "days",
                    "verified": False
                }
            ]
        }
        now = datetime.datetime.now()
        response = self._post_json(reverse('accept_results'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(labresults.Payload.objects.count(), 1)
        payload = labresults.Payload.objects.get()
        self.assertEqual(payload.raw, json.dumps(data))
        self.assertTrue(payload.parsed_json)
        self.assertTrue(payload.validated_schema)
        self.assertEqual(user, payload.auth_user)
        self.assertEqual(payload.incoming_date.year, now.year)
        self.assertEqual(payload.incoming_date.month, now.month)
        self.assertEqual(payload.incoming_date.day, now.day)
        self.assertEqual(payload.incoming_date.hour, now.hour)

        self.assertEqual(labresults.Result.objects.count(), 2)
        result1 = labresults.Result.objects.get(sample_id="10-09998")
        result2 = labresults.Result.objects.get(sample_id="10-09997")
        # 10-09999 will not make it in because it's missing a pat_id
        self.assertEqual(result1.payload, payload)
        self.assertEqual(result2.payload, payload)
        self.assertTrue(result1.verified)
        self.assertEqual(result1.child_age_unit, 'weeks')
        self.assertFalse(result2.verified)
        self.assertEqual(result2.child_age_unit, 'days')

    def test_payload_missing_fac(self):
        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='labresults',
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
        response = self._post_json(reverse('accept_results'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(labresults.Payload.objects.count(), 1)
        payload = labresults.Payload.objects.get()
        self.assertEqual(payload.raw, json.dumps(data))
        self.assertTrue(payload.parsed_json)
        self.assertTrue(payload.validated_schema)
        self.assertEqual(labresults.Result.objects.count(), 1)
        self.assertEqual(labresults.LabLog.objects.count(), 1)

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

    def test_results_changed_notification(self):        
        """
        Tests sending of notifications for previously sent later change in either
        requisition id, or actual results (from or to Positive/Negative). One
        notification goes to all clinic workers and another to all support staff.
        """
        # Scheduled task will not run on a weekend
        if is_today_a_weekend():
            return
        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='labresults',
                                      codename='add_payload')
        user.user_permissions.add(perm)
        self.client.login(username='adh', password='abc')
        
        # get results from initial payload
        self._post_json(reverse('accept_results'), INITIAL_PAYLOAD)

        # let the clinic worker get the results
        script = """
            clinic_worker > CHECK RESULTS
            clinic_worker < Hello John Banda. We have 3 DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results.
            clinic_worker > 4567
            clinic_worker < Thank you! Here are your results: **** 1029023412;NotDetected. **** 78;NotDetected. **** 21234987;NotDetected
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again John Banda!
            """        
        self.runScript(script)

        # testing if the payload is processed fine is done in other test methods

        # process changed payload with changes in results and one req_id
        self._post_json(reverse('accept_results'), CHANGED_PAYLOAD)

        sent_results = Result.objects.filter(notification_status='updated')
        for sent_result in sent_results:
            self.assertTrue(sent_result.result_sent_date != None)

        # The number of results records should remain to be 3
        self.assertEqual(labresults.Result.objects.count(), 3)

        # Start router and manually call send_changed_records_notification()
        self.startRouter()
        tasks.send_changed_records_notification(self.router)

        # Get all the messages sent
        msgs = self.receiveAllMessages()
        self.stopRouter()
        # Since we have 2 clinic workers we expect 2 URGENT messages to be sent
        # to them. A follow-up message should be sent to the support staff
        msg1 = msg2 = "URGENT: Some results sent to your clinic have changed. Please send your pin, get the new results and update your logbooks."
        msg3 = "Make a followup for changed results Mibenge Clinic: ID=1029023412, Result=R, old value=N;****ID=87, Result=P, old value=78:N;****ID=21234987b, Result=N, old value=21234987. Contacts = John Banda:clinic_worker, Mary Phiri:other_worker"
        self.assertEqual(msg1,msgs[0].text)
        self.assertEqual(msg2,msgs[1].text)
        self.assertEqual(msg3,msgs[2].text)
        self.assertEqual("John Banda",msgs[0].connection.contact.name)
        self.assertEqual("Mary Phiri",msgs[1].connection.contact.name)
        self.assertEqual("Help Admin",msgs[2].connection.contact.name)
        self.assertEqual("Help Admin2",msgs[3].connection.contact.name)

        # clinic_worker should be able to get the results by replying with PIN
        script = """
            clinic_worker > 4567
            other_worker  < John Banda has collected these results
            clinic_worker < Thank you! Here are your results: **** 1029023412;Rejected. **** 78;NotDetected changed to 87;Detected
            clinic_worker < **** 21234987;NotDetected changed to 21234987b;NotDetected
            clinic_worker < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again John Banda!
            """
        self.runScript(script)
        self.assertEqual(0,Result.objects.filter(notification_status='sent',
                            result_sent_date=None).count())

    def test_send_results_notification(self):
        """
        Tests sending of notifications for new results.
        """
        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='labresults',
                                      codename='add_payload')
        user.user_permissions.add(perm)
        self.client.login(username='adh', password='abc')

        # get results from a payload
        self._post_json(reverse('accept_results'), INITIAL_PAYLOAD)

        # The number of results records should be 3
        self.assertEqual(labresults.Result.objects.count(), 3)

        # start router and send a notification
        self.startRouter()
        tasks.send_results_notification(self.router)

        # Get all the messages sent
        msgs = self.receiveAllMessages()
        self.stopRouter()

        msg1 = "Hello Mary Phiri. We have 3 DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results."
        msg2 = "Hello John Banda. We have 3 DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results."

        self.assertTrue(msg1 in (msgs[0].text, msgs[1].text ),
        "Following message was not sent:\n%s" % msg1)
        self.assertTrue(msg2 in (msgs[0].text, msgs[1].text ),
        "Following message was not sent:\n%s" % msg2)
        self.assertEqual(2,len(msgs))

        # let clinic worker also become a cba, let other worker leave
        script = """
            clinic_worker > agent 402029 3 John Banda
            clinic_worker  < Thank you John Banda! You have successfully registered as a RemindMi Agent for zone 3 of Mibenge Clinic.
            other_worker > leave
            other_worker  < You have successfully unregistered, Mary Phiri. We're sorry to see you go.
            """
        self.runScript(script)

        # start router and send a notification
        self.startRouter()
        tasks.send_results_notification(self.router)

        # Get all the messages sent
        msgs = self.receiveAllMessages()
        
        self.assertEqual(1,len(msgs))
        self.assertEqual(msg2,msgs[0].text)

        self.assertEqual(0, Result.objects.filter(notification_status='sent',
                            result_sent_date=None).count())
        self.assertEqual(0, Result.objects.filter(
                            arrival_date=None).exclude(result=None).count())
        time.sleep(1)
        self.stopRouter()
