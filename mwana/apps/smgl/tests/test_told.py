from mwana.apps.smgl.tests.shared import SMGLSetUp
from mwana.apps.smgl.models import ReminderNotification, ToldReminder
from mwana.apps.smgl.models import TOLD_TYPE_CHOICES
from mwana.apps.smgl import const
from datetime import datetime, timedelta
from mwana.apps.smgl.tests.shared import create_birth_registration, \
    create_facility_visit, create_referral, create_mother


class SMGLToldTestCase(SMGLSetUp):
    fixtures = ["initial_data.json"]

    def setUp(self):
        super(SMGLToldTestCase, self).setUp()
        ReminderNotification.objects.all().delete()

        self.createDefaults()
        self.user_number = "15"
        self.name = "AntonDA"
        self.cba = self.createUser("cba", "456", location="80402404")

    def testValidTold(self):
        mom = create_mother()
        told_reminders = ToldReminder.objects.filter(mother=mom)
        self.assertEqual(0, told_reminders.count())
        create_facility_visit(data={'mother': mom})
        create_referral(data={'mother': mom})

        resp = const.TOLD_COMPLETE % {"name": self.name, "unique_id":mom.uid}
        for told_type in TOLD_TYPE_CHOICES:
            script = """
                %(num)s > told %(muid)s %(type)s
                %(num)s < %(resp)s
            """ % {"num": self.user_number, "muid": mom.uid,
                   "resp": resp, "type": told_type[0]}
            self.runScript(script)
            self.assertSessionSuccess()

        told_reminders = ToldReminder.objects.filter(mother=mom)
        self.assertEqual(3, told_reminders.count())

    def testInvalidToldEDD(self):
        mom = create_mother()
        create_birth_registration(data={'mother': mom})

        resp = const.TOLD_MOTHER_HAS_ALREADY_DELIVERED % {"unique_id": mom.uid}
        script = """
            %(num)s > told %(muid)s EDD
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "muid": mom.uid, "resp": resp}
        self.runScript(script)
        self.assertSessionFail()
        told_reminders = ToldReminder.objects.filter(mother=mom)
        self.assertEqual(0, told_reminders.count())

    def testInvalidToldNVD(self):
        mom = create_mother()
        create_facility_visit(data={'mother': mom,
            'next_visit': (datetime.now() - timedelta(days=30)).date(),
                })

        resp = const.TOLD_MOTHER_HAS_NO_NVD % {"unique_id": mom.uid}
        script = """
            %(num)s > told %(muid)s NVD
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "muid": mom.uid, "resp": resp}
        self.runScript(script)
        self.assertSessionFail()
        told_reminders = ToldReminder.objects.filter(mother=mom)
        self.assertEqual(0, told_reminders.count())

    def testInvalidToldREF(self):
        mom = create_mother()
        create_referral(data={'mother': mom,
            'date': (datetime.now() - timedelta(days=30)).date(),
                })

        resp = const.TOLD_MOTHER_HAS_NO_REF % {"unique_id": mom.uid}
        script = """
            %(num)s > told %(muid)s REF
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "muid": mom.uid, "resp": resp}
        self.runScript(script)
        self.assertSessionFail()
        told_reminders = ToldReminder.objects.filter(mother=mom)
        self.assertEqual(0, told_reminders.count())

    def testBadTold(self):
        bad_code_resp = 'Answer must be one of the choices for "Type of reminder, choices: edd, nvd, ref, pp"'
        mom = create_mother()
        told_reminders = ToldReminder.objects.filter(mother=mom)
        self.assertEqual(0, told_reminders.count())

        script = """
            %(num)s > told %(muid)s invalidcode
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "muid": mom.uid, "resp": bad_code_resp}
        self.runScript(script)
        # self.assertSessionFail() # FIXME: real failure
        told_reminders = ToldReminder.objects.filter(mother=mom)
        self.assertEqual(0, told_reminders.count())

    def testToldNotRegistered(self):
        script = """
            %(num)s > told mothernotregistered edd
            %(num)s < %(resp)s
        """ % {"num": "notacontact", "resp": const.NOT_REGISTERED}
        self.runScript(script)
        self.assertSessionFail()
