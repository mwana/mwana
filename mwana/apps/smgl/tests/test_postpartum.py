from mwana.apps.smgl.tests.shared import SMGLSetUp, create_facility_visit,\
    create_birth_registration
from mwana.apps.smgl.models import PregnantMother, FacilityVisit,\
    ReminderNotification
from mwana.apps.smgl import const
from datetime import datetime, timedelta
from mwana.apps.smgl.reminders import send_followup_reminders,\
    send_upcoming_delivery_reminders
from mwana.apps.smgl.app import BIRTH_REG_RESPONSE


class SMGLPostPartumTest(SMGLSetUp):
    fixtures = ["initial_data.json"]

    def setUp(self):
        super(SMGLPostPartumTest, self).setUp()
        ReminderNotification.objects.all().delete()

        self.createDefaults()
        self.user_number = "15"
        self.name = "AntonDA"
        self.cba = self.createUser("cba", "456", location="80402404")

        self.assertEqual(0, PregnantMother.objects.count())
        self.assertEqual(0, FacilityVisit.objects.count())


    def testRegister(self):
        resp = const.MOTHER_SUCCESS_REGISTERED % {"name": self.name,
                                                  "unique_id": "80403000000112"}
        script = """
            %(num)s > REG 80403000000112 Mary Soko none %(tomorrow)s R 80402404 %(earlier)s %(later)s
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp,
               "tomorrow": self.tomorrow.strftime("%d %m %Y"),
               "earlier": self.earlier.strftime("%d %m %Y"),
               "later": self.later.strftime("%d %m %Y")}
        self.runScript(script)

        self.assertEqual(1, PregnantMother.objects.count())
        mom = PregnantMother.objects.get(uid='80403000000112')
        self.assertEqual(self.user_number, mom.contact.default_connection.identity)
        self.assertEqual("Mary", mom.first_name)
        self.assertEqual("Soko", mom.last_name)
        self.assertEqual(self.earlier, mom.lmp)
        self.assertEqual(self.later, mom.edd)
        self.assertEqual(self.tomorrow, mom.next_visit)
        self.assertTrue(mom.risk_reason_none)
        self.assertEqual(["none"], list(mom.get_risk_reasons()))
        self.assertEqual("r", mom.reason_for_visit)

        self.assertEqual(0, FacilityVisit.objects.count())



    def testPostPartum(self):
        self.testRegister()
        mom = PregnantMother.objects.get(uid='80403000000112')
        create_birth_registration(data={"mother": mom})
        resp = const.PP_COMPLETE % {"name": self.name,
                                   "unique_id": "80403000000112"}
        script = """
            %(num)s > PP 80403000000112 WELL WELL NO %(tomorrow)s
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp,
               "tomorrow": self.tomorrow.strftime("%d %m %Y")
                }
        self.runScript(script)

        self.assertEqual(1, FacilityVisit.objects.count())

    def testPostPartumNotRegistered(self):
        script = """
            %(num)s > PP 80403000000112 WELL WELL NO %(tomorrow)s
            %(num)s < %(resp)s
        """ % {"num": "notacontact", "resp": const.NOT_REGISTERED,
               "tomorrow": self.tomorrow.strftime("%d %m %Y")
                }
        self.runScript(script)

    def testPostPartumOptionalNvd(self):
        self.testRegister()
        mom = PregnantMother.objects.get(uid='80403000000112')
        create_birth_registration(data={"mother": mom})
        create_facility_visit(data={'mother': mom, 'visit_type': 'pos'})
        create_facility_visit(data={'mother': mom, 'visit_type': 'pos'})
        resp = const.PP_COMPLETE % {"name": self.name,
                                   "unique_id": "80403000000112"}
        script = """
            %(num)s > PP 80403000000112 WELL WELL NO
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp}
        self.runScript(script)

        self.assertEqual(3, FacilityVisit.objects.count())

    def testPostPartumBadNvd(self):
        self.testRegister()
        mom = PregnantMother.objects.get(uid='80403000000112')
        create_birth_registration(data={"mother": mom})
        resp = const.DATE_INCORRECTLY_FORMATTED_GENERAL % {"date_name": "Next Visit"}
        script = """
            %(num)s > PP 80403000000112 WELL WELL NO not a date
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp}
        self.runScript(script)

        self.assertEqual(0, FacilityVisit.objects.count())

    def testDatesInPast(self):
        self.testRegister()
        mom = PregnantMother.objects.get(uid='80403000000112')
        create_birth_registration(data={"mother": mom})

        yesterday = (datetime.now() - timedelta(days=1)).date()

        # next visit in past
        script = """
            %(num)s > PP 80403000000112 WELL WELL NO %(past)s
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "past": yesterday.strftime("%d %m %Y"),
               "resp": const.DATE_MUST_BE_IN_FUTURE % {"date_name": "Next Visit",
                                                       "date": yesterday}}
        self.runScript(script)
