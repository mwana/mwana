from mwana.apps.smgl.tests.shared import SMGLSetUp, get_last_session
from mwana.apps.smgl.app import BIRTH_REG_RESPONSE
from mwana.apps.smgl.models import BirthRegistration, FacilityVisit
from datetime import date, datetime, timedelta
from mwana.apps.smgl import const


class SMGLBirthRegTest(SMGLSetUp):
    fixtures = ["initial_data.json"]

    def setUp(self):
        super(SMGLBirthRegTest, self).setUp()
        self.createDefaults()
        self.user_number = "123"
        self.name = "Anton"
        self.createUser("worker", self.user_number)
        BirthRegistration.objects.all().delete()

        # also create a default mom to use
        resp = const.MOTHER_SUCCESS_REGISTERED % {"name": "AntonDA",
                                                  "unique_id": "1234"}
        yesterday = (datetime.now() - timedelta(days=1)).date()
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        script = """
            %(num)s > REG 1234 Mary Soko none %(future)s R 80402404 %(past)s %(future)s
            %(num)s < %(resp)s
        """ % {"num": "15", "past": yesterday.strftime("%d %m %Y"),
                "future": tomorrow.strftime("%d %m %Y"), "resp": resp}
        self.runScript(script)

    # TODO: beef these up. Just testing the basic workflow
    def testBasicBirthReg(self):
        self.assertEqual(0, BirthRegistration.objects.count())
        resp = BIRTH_REG_RESPONSE % {"name": self.name,
                                     "unique_id": "1234"}
        script = """
            %(num)s > birth 1234 01 01 2012 bo h yes t2
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp}
        self.runScript(script)
        self.assertEqual(1, BirthRegistration.objects.count())
        [reg] = BirthRegistration.objects.all()
        self.assertEqual("1234", reg.mother.uid)
        self.assertEqual(date(2012, 1, 1), reg.date)
        self.assertEqual("bo", reg.gender)
        self.assertEqual("h", reg.place)
        self.assertEqual(True, reg.complications)
        self.assertEqual(2, reg.number)
        self.assertSessionSuccess()

    def testBirthFacilityVisit(self):
        self.testBasicBirthReg()
        #Check for facility visit
        self.assertEqual(1, FacilityVisit.objects.filter(visit_type='pos').count())


    def testBirthNotRegistered(self):
        script = """
            %(num)s > birth 1234 01 01 2012 bo h yes t2
            %(num)s < %(resp)s
        """ % {"num": "notacontact", "resp": const.NOT_REGISTERED}
        self.runScript(script)
        self.assertSessionFail()

    def testDOBInPast(self):
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        script = """
            %(num)s > birth 1234 %(date)s bo h yes t2
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "date": tomorrow.strftime("%d %m %Y"),
               "resp": const.DATE_MUST_BE_IN_PAST % {"date_name": "Date of Birth",
                                                      "date": tomorrow}}
        self.runScript(script)
        self.assertSessionFail()

    def testOptionalLastQuestion(self):
        resp = BIRTH_REG_RESPONSE % {"name": self.name, "unique_id":1234}
        script = """
            %(num)s > birth 1234 01 01 2012 gi f yes
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp}
        self.runScript(script)
        self.assertEqual(1, BirthRegistration.objects.count())
        [reg] = BirthRegistration.objects.all()
        self.assertEqual("1234", reg.mother.uid)
        self.assertEqual(date(2012, 1, 1), reg.date)
        self.assertEqual("gi", reg.gender)
        self.assertEqual("f", reg.place)
        self.assertEqual(True, reg.complications)
        self.assertEqual(1, reg.number)
        self.assertSessionSuccess()

    def testNoMother(self):
        resp = BIRTH_REG_RESPONSE % {"name": self.name,
                                     "unique_id": "none"}
        script = """
            %(num)s > birth none 01 01 2012 gi f yes
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp}
        self.runScript(script)
        self.assertEqual(1, BirthRegistration.objects.count())
        [reg] = BirthRegistration.objects.all()
        self.assertEqual(None, reg.mother)
        self.assertSessionSuccess()

    def testBadMotherId(self):
        resp = const.MOTHER_NOT_FOUND %{"unique_id": "12345"}
        script = """
            %(num)s > birth 12345 01 01 2012 gi f yes
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp}
        self.runScript(script)
        self.assertEqual(0, BirthRegistration.objects.count())
        self.assertSessionFail()
