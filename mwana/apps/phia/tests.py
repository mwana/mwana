# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.phia.models import Result
import time
import json

import datetime
import mwana.const as const
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings
from mwana.apps.phia import models as phia
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from rapidsms.models import Connection, Contact
from mwana.apps.phia import tasks
from mwana.apps.phia.testdata.payloads import INITIAL_PAYLOAD


class PhiaSetUp(TestScript):

    def setUp(self):
        # this call is required if you want to override setUp
        super(PhiaSetUp, self).setUp()
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
        self.contact.types.add(const.get_phia_worker_type())

        connection.contact = self.contact
        connection.save()

        # create another one
        self.other_contact = Contact.objects.create(alias="mary", name="Mary Phiri",
                                                    location=self.clinic, pin="6789")
        self.other_contact.types.add(const.get_phia_worker_type())

        Connection.objects.create(identity="other_worker", backend=connection.backend,
                                  contact=self.other_contact)
        connection.save()

        # create another worker for a different clinic
        self.central_clinic_worker = Contact.objects.create(alias="jp", name="James Phiri",
                                                    location=self.mansa_central, pin="1111")
        self.central_clinic_worker.types.add(const.get_phia_worker_type())

        Connection.objects.create(identity="central_clinic_worker", backend=connection.backend,
                                  contact=self.central_clinic_worker)
        connection.save()

        # create a worker for the live_results_true clinic
        self.true_clinic_worker = Contact.objects.create(alias="jbt", name="John Banda",
                                        location=self.clinic_live_results_true, pin="1001")
        self.true_clinic_worker.types.add(const.get_phia_worker_type())

        Connection.objects.create(identity="true_clinic_worker", backend=connection.backend,
                                    contact=self.true_clinic_worker)

        # create a worker for the live_results_false clinic
        self.false_clinic_worker = Contact.objects.create(alias="jbf", name="John Banda",
                                        location=self.clinic_live_results_false, pin="0110")
        self.false_clinic_worker.types.add(const.get_phia_worker_type())

        Connection.objects.create(identity="false_clinic_worker", backend=connection.backend,
                                    contact=self.false_clinic_worker)

        # create support staff
        self.support_contact = Contact.objects.create(alias="ha1", name="Help Admin",
                                                    location=self.support_clinic, pin="1111", is_help_admin=True)
        self.support_contact.types.add(const.get_phia_worker_type())

        Connection.objects.create(identity="support_contact", backend=connection.backend,
                                  contact=self.support_contact)
        connection.save()

        # create second support staff
        self.support_contact2 = Contact.objects.create(alias="ha2", name="Help Admin2",
                                                    location=self.support_clinic, pin="2222", is_help_admin=True)
        self.support_contact2.types.add(const.get_phia_worker_type())

        Connection.objects.create(identity="support_contact2", backend=connection.backend,
                                  contact=self.support_contact2)
        connection.save()

    def tearDown(self):
        # this call is required if you want to override tearDown
        super(PhiaSetUp, self).tearDown()
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
        self.assertTrue(const.get_phia_worker_type() in contact.types.all())



class TestApp(TestScript):
#    apps = (cleaner_App, handler_app, )
   
    def testWorkflows(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        dst = LocationType.objects.create(slug=const.DISTRICT_SLUGS[0])
        prv = LocationType.objects.create(slug=const.PROVINCE_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        central_clinic = Location.objects.create(name="Central Clinic",
                                                 slug="403012", type=ctr,
                                                 send_live_results=True)
        mansa = Location.objects.create(name="Mansa",
                                        slug="403000", type=dst)
        luapula = Location.objects.create(name="Luapula",
                                          slug="400000", type=prv)
       
        

        script = """
            jb > join clinic 4o30i2 jacob banda 1234
            jb < Hi Jacob Banda, thanks for registering for Results160 from Central Clinic. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            kk > join clinic 4f30i2 kenneth kaunda 1234
            kk < Sorry, I don't know about a location with code 4f3012. Please check your code and try again.
        """
        self.runScript(script)
        time.sleep(1)
        self.assertEqual(1, Contact.objects.count())
        jb = Contact.objects.get(name='Jacob Banda')
        self.assertEqual(central_clinic, jb.location)
        self.assertEqual(jb.types.count(), 1)
        self.assertEqual(jb.types.all()[0].slug, const.CLINIC_WORKER_SLUG)

        script = """
            hubman > join hub 4o30i2 hubman banda 1234
            hubman < Hi Hubman Banda, thanks for registering for Results160 from hub at Central Clinic. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            dho > join dho 4030 Dho banda 1234
            dho < Hi Dho Banda, thanks for registering for Results160 from Mansa DHO. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            pho > join pho 40 Pho banda 1234
            pho < Hi Pho Banda, thanks for registering for Results160 from Luapula PHO. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            labman > join lab 4o30i2 mark zuckerberg 1234
            labman < Hi Mark Zuckerberg, thanks for registering for Results160 from lab at Central Clinic. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            kdh_man > join phia kdh James Bond 1234
            kdh_man < Hi James Bond, thanks for registering as a ZAMPHIA2020 RoR & LTC SMS user at Kafue District Hospital. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)
        

        script = """
            phia_man > join phia 403012 broken hill 2345
            phia_man < Hi Broken Hill, thanks for registering as a ZAMPHIA2020 RoR & LTC SMS user at Central Clinic. Your PIN is 2345. Reply with keyword 'HELP' if this is incorrect
            phia_lady > join phia 403012 lady gaga 2345
            phia_lady < Hi Lady Gaga, thanks for registering as a ZAMPHIA2020 RoR & LTC SMS user at Central Clinic. Your PIN is 2345. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)
        time.sleep(.5)
        self.assertEqual(8, Contact.objects.count())
        phiaman = Contact.objects.get(name='Broken Hill')
        self.assertEqual(phiaman.types.all()[0].slug, const.PHIA_WORKER_SLUG)
     

        Result.objects.create(clinic=phiaman.clinic, requisition_id="1234567",
        fname=settings.GET_CLEANED_TEXT("Banana"),
        lname=settings.GET_CLEANED_TEXT("Nkonde"),
        address=settings.GET_CLEANED_TEXT("14 Munali, Lusaka"),
        sample_id='1', vl='250', cd4 = 600, notification_status='new')
        script = """
            stranger > LTC NEW
            stranger < Please send the keyword HELP if you need to be assisted.
            phia_man > LTC NEW
            phia_man < Please specify one valid temporary ID
            phia_man > LTC NEW 123456
            phia_man < There is no record with ID 123456 to link. Make sure you typed the ID correctly and try again.
            phia_man > LTC NEW 1234567
            phia_man < Please reply with your PIN to save linkage for 1234567
            phia_man > 1111
            phia_man < Sorry, that was not the correct pin code. Your pin code is a 4-digit number like 1234. If you forgot your pin code, reply with keyword 'HELP'
            phia_man > 2345
            phia_man < Clinical interaction for 1234567 confirmed
            """
        self.runScript(script)
       
        script = """
            phia_man > ROR DEMO 403012
            phia_man < Central Clinic has 3 results ready. Please reply with your pin code to retrieve them.
            phia_lady < Central Clinic has 3 results ready. Please reply with your pin code to retrieve them.
            phia_man > 234
            phia_man < Sorry, that was not the correct pin code. Your pin code is a 4-digit number like 1234. If you forgot your pin code, reply with keyword 'HELP'
            phia_man > 2345
            phia_lady < Broken Hill has collected these results
            phia_man < Here are your results: **** 9990;CD200;VL500. **** 9991;CD250;VL300. **** 9992;CD650;VL100
            phia_man < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again Broken Hill!
            phia_lady > 2345
            phia_lady < Hello Lady Gaga. Are you trying to retrieve new results? There are no new results ready for you. We shall let you know as soon as they are ready.
            """
        self.runScript(script)

      
        script = """
            stranger > ROR CHECK
            stranger < Please send the keyword HELP if you need to be assisted.
            phia_man > ROR CHECK
            phia_man < Central Clinic has 1 results ready. Please reply with your PIN code to retrieve them.
            phia_man > ROR CHECK 403012
            phia_man < Central Clinic has no new results ready right now for 403012. You will be notified when new results are ready.
            phia_man > ROR CHECK Demo9990
            phia_man < Please reply with your PIN to view the results for Demo9990
            phia_man > 12
            phia_man < Sorry, that was not the correct pin code. Your pin code is a 4-digit number like 1234. If you forgot your pin code, reply with keyword 'HELP'
            phia_man > 2345
            phia_man < Here are your results: **** Demo9990;CD200;VL500.
            phia_man > ROR CHECK DEMO9991
            phia_man < Please reply with your PIN to view the results for DEMO9991
            phia_man > 2345
            phia_man < Here are your results: **** DEMO9991;CD200;VL500.
            phia_man > ROR CHECK 1234567
            phia_man < Please reply with your PIN to view the results for 1234567
            phia_man > 2345
            phia_man < Here are your results: **** 1234567;600;250
            """
        self.runScript(script)
        Result.objects.create(clinic=phiaman.clinic, requisition_id="1111",
        fname=settings.GET_CLEANED_TEXT("Banana"),
        lname=settings.GET_CLEANED_TEXT("Nkonde"),
        address=settings.GET_CLEANED_TEXT("14 Munali, Lusaka"),
        sample_id='1', vl='255', cd4 = 601, notification_status='new')
        Result.objects.filter(clinic=phiaman.clinic).update(notification_status='new')

        script = """
            phia_man > ROR CHECK
            phia_man < Central Clinic has 2 results ready. Please reply with your PIN code to retrieve them.
            phia_man > 2345
            phia_man < Here are your results: **** 1111;601;255. **** 1234567;600;250
            """
        self.runScript(script)

        script = """
            phia_man > LTC DEMO 403012
            phia_man < Central Clinic has 2 ALTC & 1 passive participant to link to care. Please reply with your PIN code to get details of ALTC participants.
            phia_lady < Central Clinic has 2 ALTC & 1 passive participant to link to care. Please reply with your PIN code to get details of ALTC participants.
            phia_man > 234
            phia_man < Sorry, that was not the correct pin code. Your pin code is a 4-digit number like 1234. If you forgot your pin code, reply with keyword 'HELP'
            phia_man > 2345
            phia_lady < Broken Hill has collected these results
            phia_man < LTC: Banana Nkonde;14 Munali, Lusaka;9990 ****. Sante Banda;12 Minestone, Lusaka;9991 ****
            phia_man < Please record these details in your LTC Register immediately and promptly delete them from your phone. Thank you again!
            phia_lady > 2345
            phia_lady < Hello Lady Gaga. Are you trying to retrieve new results? There are no new results ready for you. We shall let you know as soon as they are ready.
            """
        self.runScript(script)

        Result.objects.create(clinic=phiaman.clinic, requisition_id="9991",
        fname=settings.GET_CLEANED_TEXT("Sante"),
        lname=settings.GET_CLEANED_TEXT("Banda"),
        address=settings.GET_CLEANED_TEXT("12 Minestone, Lusaka"),
        sample_id='1', vl='250', cd4 = 600, notification_status='sent')
        Result.objects.filter(clinic=phiaman.clinic, requisition_id="1234567").update(notification_status='sent')
        #todo: ask for pin even for demo results
        script = """
            stranger > LTC CHECK
            stranger < Please send the keyword HELP if you need to be assisted.
            phia_man > LTC CHECK
            phia_man < Central Clinic has 2 ALTC to link to care. Please reply with your PIN code to get details of ALTC participants
            phia_man > 11
            phia_man < Sorry, that was not the correct pin code. Your pin code is a 4-digit number like 1234. If you forgot your pin code, reply with keyword 'HELP'
            phia_man > 2345
            phia_man <  LTC: **** Banana Nkonde;14 Munali, Lusaka;1111. **** Sante Banda;12 Minestone, Lusaka;9991
            phia_man <  Please record the details in your LTC immediately and DELETE them from your phone. Thank you again!
            phia_man > LTC CHECK 9990
            phia_man < There are no LTC details for participant with ID 9990 for Central Clinic. Make sure you entered the correct ID
            phia_man > LTC CHECK Demo9990
            phia_man < LTC: Banana Nkonde;14 Munali, Lusaka;Demo9990
            phia_man > LTC CHECK Demo9991
            phia_man < LTC: Banana Nkonde;14 Munali, Lusaka;Demo9991
            """
        self.runScript(script)

        

class TestResultsAcceptor(PhiaSetUp):
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
        perm = Permission.objects.get(content_type__app_label='phia',
                                      codename='add_payload')
        user.user_permissions.add(perm)
        self.client.login(username='adh', password='abc')
        data = {'varname': 'data'}
        now = datetime.datetime.now()
        response = self._post_json(reverse('phia:accept_results'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(phia.Payload.objects.count(), 1)
        payload = phia.Payload.objects.get()
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
        perm = Permission.objects.get(content_type__app_label='phia',
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
                    "sample_id": "",
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
                    "sample_id": "1029023412",
                    "dob": "2009-03-30",
                    "proc_on": "2010-04-13",
                    "child_age": 8,
                    "result_unit": "p/ML",
                    "verified": True,
                    "sample_id": 'DLU0026F-02',
                    'province': '2',
                    'district': '207',
                   
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
                    "sample_id": "212987",
                    "dob": "2010-01-12",
                    "proc_on": "2010-04-17",
                    "child_age": 4,
                    "result_unit": "p/mL",
                    "verified": False
                }
            ]
        }
        now = datetime.datetime.now()
        response = self._post_json(reverse('phia:accept_results'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(phia.Payload.objects.count(), 1)
        payload = phia.Payload.objects.get()
        self.assertEqual(payload.raw, json.dumps(data))
        self.assertTrue(payload.parsed_json)
        self.assertTrue(payload.validated_schema)
        self.assertEqual(user, payload.auth_user)
        self.assertEqual(payload.incoming_date.year, now.year)
        self.assertEqual(payload.incoming_date.month, now.month)
        self.assertEqual(payload.incoming_date.day, now.day)
        self.assertEqual(payload.incoming_date.hour, now.hour)

        self.assertEqual(phia.Result.objects.count(), 2)
        result1 = phia.Result.objects.get(sample_id="10-09998")
        result2 = phia.Result.objects.get(sample_id="10-09997")
        # 10-09999 will not make it in because it's missing a sample_id
        self.assertEqual(result1.payload, payload)
        self.assertEqual(result2.payload, payload)
        self.assertTrue(result1.verified)
        self.assertFalse(result2.verified)
        self.assertEqual(phia.Result.objects.filter(sample_id="10-09998", province='2', district='207').count(), 1)
        self.assertEqual(phia.Result.objects.filter(sample_id="10-09998").count(), 1)


    def test_payload_missing_fac(self):
        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='phia',
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
                    "sample_id": "1234",
                    "dob": "2010-02-08",
                    "proc_on": "2010-04-11",
                    "child_age": 3
                }
            ]
        }
        now = datetime.datetime.now()
        response = self._post_json(reverse('phia:accept_results', current_app='phia'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(phia.Payload.objects.count(), 1)
        payload = phia.Payload.objects.get()
        self.assertEqual(payload.raw, json.dumps(data))
        self.assertTrue(payload.parsed_json)
        self.assertTrue(payload.validated_schema)
        self.assertEqual(phia.Result.objects.count(), 1)

    def test_payload_login_required(self):
        data = {'varname': 'data'}
        response = self._post_json(reverse('phia:accept_results', current_app='phia'), data)
        self.assertEqual(response.status_code, 401) # authorization required
        self.assertEqual(phia.Payload.objects.count(), 0)

    def test_payload_permission_required(self):
        User.objects.create_user(username='adh', email='', password='abc')
        self.client.login(username='adh', password='abc')
        data = {'varname': 'data'}
        response = self._post_json(reverse('phia:accept_results', current_app='phia'), data)
        self.assertEqual(response.status_code, 401) # authorization required
        self.assertEqual(phia.Payload.objects.count(), 0)

    def test_payload_post_required(self):
        response = self.client.get(reverse('phia:accept_results', current_app='phia'))
        self.assertEqual(response.status_code, 405) # method not supported

    def create_payload_auther_login(self):
        """
        Tests sending of notifications for previously sent results but later
        change in locaion.
        """

        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='phia',
                                      codename='add_payload')
        user.user_permissions.add(perm)
        self.client.login(username='adh', password='abc')

    def test_send_results_notification(self):
        """
        Tests sending of notifications for new results.
        """
        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='phia',
                                      codename='add_payload')
        user.user_permissions.add(perm)
        self.client.login(username='adh', password='abc')

        # get results from a payload
        self._post_json(reverse('phia:accept_results'), INITIAL_PAYLOAD)

        # The number of results records should be 3
        self.assertEqual(phia.Result.objects.count(), 4)
        # self.assertEqual(phia.Result.objects.exclude(phone=None).exclude(phone='').count(), 1)
        self.assertEqual(phia.Result.objects.filter(clinic=self.clinic).count(), 4)

        time.sleep(.2)
        # start router and send a notification
        self.startRouter()
        tasks.send_phia_results_notification(self.router)

        # Get all the messages sent
        msgs = self.receiveAllMessages()
        self.stopRouter()
        self.assertEqual(2, len(msgs))

        msg1 = "Mibenge Clinic has 3 results ready. Please reply with your pin code to retrieve them."
        msg2 = "Mibenge Clinic has 3 results ready. Please reply with your pin code to retrieve them."

        self.assertTrue(msg1 in (msgs[0].text, msgs[1].text ),
        "Following message was not sent:\n%s" % msg1)
        self.assertTrue(msg2 in (msgs[0].text, msgs[1].text ),
        "Following message was not sent:\n%s" % msg2)
        self.assertEqual(2, len(msgs))
        self.assertEqual(3, Result.objects.filter(notification_status='notified').count())

        time.sleep(.1)

        script = """
            other_worker > 6789
            other_worker < Here are your results: **** tempID3;;800cp/ml. **** tempID1;780;400cp/ml. **** tempID2;780;
            +260978656561 < Your appointment is due at Mibenge Clinic. If you got this msg by mistake please ignore
            +260978656562 < Your appointment is due at Mibenge Clinic. If you got this msg by mistake please ignore
            clinic_worker < Mary Phiri has collected these results
            other_worker < Please record these results in your clinic records and promptly delete them from your phone.
        """
        time.sleep(1)
        self.runScript(script)
        # r = Result()
        # r.result_sent_date

        self.assertEqual(2, Result.objects.exclude(date_participant_notified=None).count())
        self.assertEqual(3, Result.objects.exclude(who_retrieved=None).count())
        self.assertEqual(3, Result.objects.exclude(result_sent_date=None).count())
        self.assertEqual(3, Result.objects.filter(notification_status='sent').count())

        # If for some reason eligible participants did not get notifications
        Result.objects.all().update(date_participant_notified=None)
        self.startRouter()
        tasks.send_results_ready_notification_to_participant(self.router)

        # Get all the messages sent
        msgs = self.receiveAllMessages()
        self.stopRouter()

        msg = "Your appointment is due at Mibenge Clinic. If you got this msg by mistake please ignore"
        self.assertEqual(2, len(msgs))
        self.assertEqual(msg, msgs[0].text)
        self.assertEqual(msg, msgs[1].text)
        self.assertEqual('+260978656561', msgs[0].connection.identity)
        self.assertEqual('+260978656562', msgs[1].connection.identity)

        # Result.objects.filter(notification_status='notified').update(notification_status='sent')
        # start router and send a notification
        self.startRouter()
        tasks.send_tlc_details_notification(self.router)

        # Get all the messages sent
        msgs = self.receiveAllMessages()

        msg = "Mibenge Clinic has 3 ALTC participants to link to care. Please reply with your PIN code to get details of ALTC participants."
        self.assertEqual(2, len(msgs))
        self.assertEqual(msg, msgs[0].text)
        self.assertEqual(msg, msgs[1].text)

        time.sleep(1)
        self.stopRouter()

        script = """
            other_worker > 6789
            clinic_worker < Mary Phiri has collected LTC details for tempID3, tempID1, tempID2
            other_worker < LTC: **** James ;Lusaka;tempID3. **** Banana Nkonde;23 Los Angeles;tempID1. **** Love Nkonde;Lusaka;tempID2
            other_worker < Please record the details in your LTC immediately and DELETE them from your phone. Thank you again!
        """
        time.sleep(1)
        self.runScript(script)


   