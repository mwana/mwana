# vim: ai ts=4 sts=4 et sw=4

from django.conf import settings
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.testdata.reports import *
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
import mwana.const as const
from rapidsms.models import Connection
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript


class TestsSetUp(TestScript):

    def _result_text(self):
        """
        Returns the appropriate display value for DBS results as it would
        appear in an SMS.
        """
        results_text = getattr(settings, 'RESULTS160_RESULT_DISPLAY', {})
        results = {'detected': results_text.get('P', 'Detected'),
            'not_detected': results_text.get('N', 'NotDetected')}
        return results

    def setUp(self):
        # this call is required if you want to override setUp
        super(TestsSetUp, self).setUp()
        self.type = LocationType.objects.get_or_create(singular="clinic", plural="clinics", slug=const.CLINIC_SLUGS[2])[0]
        self.type1 = LocationType.objects.get_or_create(singular="district", plural="districts", slug="districts")[0]
        self.type2 = LocationType.objects.get_or_create(singular="province", plural="provinces", slug="provinces")[0]
        self.luapula = Location.objects.create(type=self.type2, name="Luapula Province", slug="400000")
        self.mansa = Location.objects.create(type=self.type1, name="Mansa District", slug="403000", parent=self.luapula)
        self.samfya = Location.objects.create(type=self.type1, name="Samfya District", slug="samfya", parent=self.luapula)
        self.clinic = Location.objects.create(type=self.type, name="Mibenge Clinic", slug="402029", parent=self.samfya, send_live_results=True)
        self.mansa_central = Location.objects.create(type=self.type, name="Central Clinic", slug="403012", parent=self.mansa, send_live_results=True)
        # clinic for send_live_results = True
        self.clinic_live_results_true = Location.objects.create(type=self.type, name="LiveResultsTrue Clinic", slug="403010", parent=self.mansa, send_live_results=True)
        # clinic for send_live_results = False
        self.clinic_live_results_false = Location.objects.create(type=self.type, name="LiveResultsFalse Clinic", slug="403011", parent=self.mansa, send_live_results=False)

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

        # create cba
        script = """
            cba> JOIN CBA 402029 4 Mary Phiri
            hub_worker> JOIN hub 402029 James Shula 1111
            dho> JOIN dho 403000 Chuchu Banda 1111
            pho> JOIN pho 400000 Chali Mutale 1111
        """
        self.runScript(script)

    def tearDown(self):
        # this call is required if you want to override tearDown
        super(TestsSetUp, self).tearDown()
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


class UnkownWorkerTestApp(TestsSetUp):

    def testGeneralErrors(self):      

        # Error from unregistered user
        script = """
            unknown_worker > what is my name
            unknown_worker < Invalid Keyword. Please send the keyword HELP if you need to be assisted.
        """
        self.runScript(script)

class CbaWorkerTestApp(TestsSetUp):

    def testGeneralErrors(self):

         # Test inclusion of RemindMi
        script = """
            cba > what am I trying to do?
            cba < Invalid Keyword. Valid keywords are BIRTH, MWANA, TOLD, CONFIRM, MSG CBA, MSG CLINIC and MSG ALL. Respond with any keyword or HELP for more information.
        """
        self.runScript(script)

         # Test inclusion of RemindMi
        script = """
            cba > Remindmi  + 260978775414  mwana  13/09/2010. Baeuty  chishala
            cba < Sorry Mary Phiri, we didn't understand that message. Send the keyword HELP if you need to be helped.
        """
        self.runScript(script)
        script = """
            cba > to remindmi +260978775414 msgclinic nilisa uci kuno ku zone 1
            cba < Sorry Mary Phiri, we didn't understand that message. Send the keyword HELP if you need to be helped.
        """
        self.runScript(script)

class PhoWorkerTestApp(TestsSetUp):

    def testGeneralErrors(self):

         # Test inclusion of RemindMi
        script = """
            pho > what am I trying to do?
            pho < Sorry Chali Mutale. Respond with keyword HELP for assistance.
        """
        self.runScript(script)

class DhoWorkerTestApp(TestsSetUp):

    def testGeneralErrors(self):

         # Test inclusion of RemindMi
        script = """
            dho > what am I trying to do?
            dho < Invalid Keyword. Valid keywords MSG DHO, MSG CLINIC and MSG ALL. Respond with any keyword or HELP for more information.
        """
        self.runScript(script)

class HubWorkerTestApp(TestsSetUp):

    def testGeneralErrors(self):

         # Test inclusion of RemindMi
        script = """
            hub_worker > what am I trying to do?
            hub_worker < Invalid Keyword. Valid keywords are RECEIVED and SENT. Respond with any keyword or HELP for more information
        """
        self.runScript(script)


class ClinicWorkerTestApp(TestsSetUp):

    def testGeneralErrors(self):

        # Test inclusion of Results 160
        script = """
            clinic_worker > Results 160 ,my PIN  NUMBER is 2332. Kindly send DBS results.
            clinic_worker < Sorry, we didn't understand that message. Send the keyword HELP if you need to be helped.
        """
        self.runScript(script)


        #
        script = """
            clinic_worker > what is my name
            clinic_worker < Invalid Keyword. Valid keywords are CHECK, RESULT, SENT, TRACE, MSG CBA, MSG CLINIC, MSG ALL and MSG DHO. Respond with any keyword or HELP for more information
        """
        self.runScript(script)

    def testSendingPinAtWrongTime(self):
        """
        User sends a four digit PIN. But the user is not in labresults'
        'waiting_for_pin'. I.e the system is not in a state of waiting for user
        PINS
        """


        # CASE 1: Correct PIN, No Uncollected results exist
        script = """
            clinic_worker > 4567
            clinic_worker < Hello John Banda. Are you trying to retrieve new results? There are no new results ready for you. We shall let you know as soon as they are ready.
        """
        self.runScript(script)

        # CASE 2: Totally Wrong PIN, No Uncollected results exist
        script = """
            clinic_worker > 0000
            clinic_worker < Hello John Banda. Are you trying to retrieve new results? There are no new results ready for you. We shall let you know as soon as they are ready.
        """
        self.runScript(script)

        # create some ready results for Cases 3 and 4 below. Try each case with
        # two scenaris: (a) with new results (b) with 'notified' results
        self.assertEqual(0, Result.objects.count())

        # Scenario A: New results
        Result.objects.create(requisition_id="0001", clinic=self.clinic,
                              result="N",
                              notification_status="new")

        self.assertEqual(1, Result.objects.count())

        # CASE 3a: Totally Wrong PIN, Uncollected new results exist
        script = """
            clinic_worker > 0000
            clinic_worker < Hello John Banda. If you are trying to retrieve new results please send the keyword CHECK. Make sure you send your correct PIN when asked to.
        """
        self.runScript(script)

        # CASE 4a: Correct PIN, Uncollected new results exist
        script = """
            clinic_worker > 4567
            clinic_worker < Hello John Banda. If you are trying to retrieve new results please send the keyword CHECK.
        """
        self.runScript(script)
        
        # Scenario B: 'Notified' results
        Result.objects.all().delete()
        

        self.assertEqual(0, Result.objects.count())
        Result.objects.create(requisition_id="0001", clinic=self.clinic,
                              result="N",
                              notification_status="notified")

        self.assertEqual(1, Result.objects.count())

        # CASE 3b: Totally Wrong PIN, Uncollected notified results exist
        script = """
            clinic_worker > 0000
            clinic_worker < Hello John Banda. If you are trying to retrieve new results please send the keyword CHECK. Make sure you send your correct PIN when asked to.
        """
        self.runScript(script)

        # CASE 4b: Correct PIN, Uncollected results exist
        script = """
            clinic_worker > 4567
            clinic_worker < Sorry John Banda. If you are trying to retrieve new results please send the keyword CHECK.
        """
        self.runScript(script)


    