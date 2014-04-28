from mwana.apps.smgl.tests.shared import SMGLSetUp
from mwana.apps.smgl.models import PregnantMother, Referral
from mwana.apps.smgl import const


class SMGLBirthBugRegTest(SMGLSetUp):
    fixtures = ["initial_data.json"]

    def setUp(self):
        super(SMGLBirthBugRegTest, self).setUp()
        self.createDefaults()
        self.user_number = "15"
        self.name = "AntonDA"

    def testReg1(self):
        self.assertEqual(0, PregnantMother.objects.count())
        resp = const.MOTHER_SUCCESS_REGISTERED % {"name": self.name,
                                                  "unique_id": "804024222"}
        script = """
            %(num)s > REG 804024222 FEBBY MALAMBO OTH %(tomorrow)s R 80402402 %(earlier)s %(later)s
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp,
               "tomorrow": self.tomorrow.strftime("%d %m %Y"),
               "earlier": self.earlier.strftime("%d %m %Y"),
               "later": self.later.strftime("%d %m %Y")}

        self.runScript(script)
        self.assertEqual(1, PregnantMother.objects.count())

    def testRefer1(self):
        success_resp = const.REFERRAL_RESPONSE % {"name": self.name,
                                                  "unique_id": "8040120143",
                                                  "facility_name": "Kalomo District Hospital HAHC"}
        script = """
            %(num)s > REFER 8040120143 804030 APH 1100 NEM
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": success_resp}

        self.runScript(script)
        [referral] = Referral.objects.all()
