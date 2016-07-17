# vim: ai ts=4 sts=4 et sw=4
from datetime import date

from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from mwana.apps.vaccination.models import VaccinationSession
from mwana.apps.vaccination.models import Client
from mwana.apps.vaccination.models import Appointment
import mwana.const as const
from rapidsms.models import Connection
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript


class VaccinationSetUp(TestScript):

    def setUp(self):
        # this call is required if you want to override setUp
        super(VaccinationSetUp, self).setUp()
        self.type = LocationType.objects.get_or_create(singular="clinic", plural="clinics", slug=const.CLINIC_SLUGS[0])[0]
        self.type1 = LocationType.objects.get_or_create(singular="district", plural="districts", slug="districts")[0]
        self.type2 = LocationType.objects.get_or_create(singular="province", plural="provinces", slug="provinces")[0]
        self.type3 = LocationType.objects.get_or_create(singular="zone", plural="zones", slug=const.ZONE_SLUGS[0])[0]
        self.luapula = Location.objects.create(type=self.type2, name="Luapula Province", slug="luapula")
        self.mansa = Location.objects.create(type=self.type1, name="Mansa District", slug="mansa", parent=self.luapula)
        self.samfya = Location.objects.create(type=self.type1, name="Samfya District", slug="samfya", parent=self.luapula)
        self.clinic = Location.objects.create(type=self.type, name="Mibenge Clinic", slug="402029", parent=self.samfya, send_live_results=True)
        self.mansa_central = Location.objects.create(type=self.type, name="Central Clinic", slug="403012", parent=self.mansa, send_live_results=True)
        self.zone = Location.objects.create(type=self.type3, name="4", slug="zone4", parent=self.clinic)
        # this gets the backend and connection in the db
        script = "clinic_worker > hello world"
        self.runScript(script)
        connection = Connection.objects.get(identity="clinic_worker")

        self.contact = Contact.objects.create(alias="banda", name="John Banda",
                                              location=self.clinic, pin="4567")
        self.contact.types.add(const.get_clinic_worker_type())

        connection.contact = self.contact
        connection.save()

        # create a cba
        self.cba = Contact.objects.create(alias="mary", name="Mary Phiri",
                                          location=self.zone, )
        self.cba.types.add(const.get_cba_type())
        self.cba.save()

        cba_conn = Connection.objects.create(identity="cba", backend=connection.backend,
                                  contact=self.cba)
        cba_conn.save()

        # create another worker for a different clinic
        self.central_clinic_worker = Contact.objects.create(alias="jp", name="James Phiri",
                                                            location=self.mansa_central, pin="1111")
        self.central_clinic_worker.types.add(const.get_clinic_worker_type())

        Connection.objects.create(identity="central_clinic_worker", backend=connection.backend,
                                  contact=self.central_clinic_worker)
        connection.save()

        self.s1 = VaccinationSession.objects.get_or_create(session_id='s1', predecessor=None, min_child_age=0)[0]#BCG
        self.s2 = VaccinationSession.objects.get_or_create(session_id='s2', predecessor=None, min_child_age=0, max_child_age=13)[0]#OPV0
        self.s3 = VaccinationSession.objects.get_or_create(session_id='s3', predecessor=None, min_child_age=6 * 7)[0]#OPV1, etc
        self.s4 = VaccinationSession.objects.get_or_create(session_id='s4', predecessor=self.s3, min_child_age=4 * 7)[0]#OPV2, etc
        self.s5 = VaccinationSession.objects.get_or_create(session_id='s5', predecessor=self.s4, min_child_age=4 * 7)[0]#OPV3, etc
        self.s6 = VaccinationSession.objects.get_or_create(session_id='s6', predecessor=None, min_child_age=548)[0]#measles at 18 months
        self.s7 = VaccinationSession.objects.get_or_create(session_id='s7', predecessor=None, given_if_not_exist='s2', min_child_age=274)[0]#At 9 months, only if OPV0 was not given

    def testBootstrap(self):
        cba_contact = Contact.objects.get(id=self.cba.id)
        self.assertTrue(const.get_cba_type() in cba_contact.types.all())
        contact = Contact.objects.get(id=self.contact.id)
        self.assertEqual("clinic_worker", contact.default_connection.identity)
        self.assertEqual(self.clinic, contact.location)
        self.assertEqual("4567", contact.pin)
        self.assertTrue(const.get_clinic_worker_type() in contact.types.all())


class TestApp(VaccinationSetUp):

    def testUnregisteredUser(self):
        script = '''
            unknown > BIRTHREG 21314/16 F 2/8/2016 Jane Moonga 25
            unknown < Sorry, you must be registered before you can register a child. If you think this message is a mistake, respond with keyword 'HELP'
        '''
        self.runScript(script)

    def testBadClientNumber(self):
        script = '''
            cba > BIRTHREG 26 F 2/8/2016 Jane Moonga 25
            cba < Sorry, '26', is not a valid Child's ID. If you think this message is a mistake reply with keyword HELP.
            cba > BIRTHREG 233131313131313131316 F 2/2/2016 Jane Moonga 25
            cba < Sorry, '233131313131313131316', is not a valid Child's ID. If you think this message is a mistake reply with keyword HELP.
        '''
        self.runScript(script)

    def testBadGender(self):
        script = '''
            cba > BIRTHREG 21314/16 Fx 2/2/2016 Jane Moonga 25
            cba < Fx is not a correct value for gender. Enter gender as F or M
        '''
        self.runScript(script)

    def testBadBirthDate(self):
        script = '''
            cba > BIRTHREG 21314/16 F 49/8/2016 Jane Moonga 25
            cba < Sorry, I couldn't understand the date '49/8/2016'. Enter date like DAY/MONTH/YEAR, e.g. 17/07/2016
        '''
        self.runScript(script)

    def testFutureBirthDate(self):
        script = '''
            cba > BIRTHREG 21314/16 F 2/8/2026 Jane Moonga 25
            cba < Sorry, you cannot register a birth with a date after today's.
        '''
        self.runScript(script)

    def testBadMotherName(self):
        script = '''
            cba > BIRTHREG 21314/16 F 2/3/2016 Li 25
            cba < Sorry, 'Li', is not a valid name
            cba > BIRTHREG 21314/16 F 2/3/2016 Veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery looooooooooong name 25
            cba < Sorry, 'Veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery Looooooooooong Name', is not a valid name
        '''
        self.runScript(script)

    def testBadMotherAge(self):
        script = '''
            cba > BIRTHREG 21314/16 F 2/2/2016 Jane Moonga x
            cba < Sorry, 'x', is not a valid number for mother's age
            cba > BIRTHREG 21314/16 F 2/2/2016 Jane Moonga 12
            cba < Sorry, '12', is not a valid number for mother's age
            cba > BIRTHREG 21314/16 F 2/2/2016 Jane Moonga 52
            cba < Sorry, '52', is not a valid number for mother's age
            cba > BIRTHREG 21314/16 F 2/2/2016 Jane Moonga
            cba < Sorry, 'Moonga', is not a valid number for mother's age
        '''
        self.runScript(script)

    def testBirthRegistration(self):
        script = '''
            cba > BIRTHREG 21314/16 F 2/7/2016 jane moonga 25
            cba < Thank you Mary Phiri! You have successfully registered a baby with ID 21314/16, Gender Female, DOB 02/07/2016 for Jane Moonga aged 25.
            cba > BIRTHREG 21314/16 F 2/7/2016 jane moonga 25
            cba < Thank you Mary Phiri! You have successfully registered a baby with ID 21314/16, Gender Female, DOB 02/07/2016 for Jane Moonga aged 25.
            cba > BIRTHREG 21314/16 M 2/7/2016 jane moonga 25
            cba < There is already a baby registered with BabyID: 21314/16, Gender: Female, DOB: 02/07/2016, Mother's Name: Jane Moonga, Mother's Age: 25, Clinic: Mibenge Clinic
            cba > BIRTHREG 21314/16 F 22/6/2016 jane moonga 25
            cba < There is already a baby registered with BabyID: 21314/16, Gender: Female, DOB: 02/07/2016, Mother's Name: Jane Moonga, Mother's Age: 25, Clinic: Mibenge Clinic
            cba > BIRTHREG 21314/16 F 2/7/2016 jane mumba 25
            cba < There is already a baby registered with BabyID: 21314/16, Gender: Female, DOB: 02/07/2016, Mother's Name: Jane Moonga, Mother's Age: 25, Clinic: Mibenge Clinic
            cba > BIRTHREG 21314/16 F 2/7/2016 jane moonga 24
            cba < There is already a baby registered with BabyID: 21314/16, Gender: Female, DOB: 02/07/2016, Mother's Name: Jane Moonga, Mother's Age: 25, Clinic: Mibenge Clinic
        '''
        self.runScript(script)
        self.assertEqual(Client.objects.count(), 1)
        client = Client.objects.get(client_number='21314/16')
        self.assertTrue(client.birth_date == date(2016, 7, 2))
        self.assertEqual(client.gender, 'f')
        self.assertEqual(client.mother_name, 'Jane Moonga')
        self.assertEqual(client.mother_age, 25)
        self.assertEqual(client.location, self.zone)
        self.assertEqual(Appointment.objects.count(), 5)
        self.assertEqual(Appointment.objects.filter(client=client, cba_responsible=self.cba).count(), 5)
        self.assertEqual(Appointment.objects.filter(client=client, vaccination_session__predecessor=None).count(), 5)