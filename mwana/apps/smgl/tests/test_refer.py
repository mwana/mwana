from mwana.apps.smgl.tests.shared import SMGLSetUp
from mwana.apps.smgl.models import Referral
from mwana.apps.smgl.app import FACILITY_NOT_RECOGNIZED
from mwana.apps.locations.models import Location
from mwana.apps.smgl import const


class SMGLReferTest(SMGLSetUp):
    fixtures = ["initial_data.json"]
    
    def setUp(self):
        super(SMGLReferTest, self).setUp()
        Referral.objects.all().delete()
        self.user_number = "123"
        self.name = "Anton"
        self.createUser("worker", self.user_number)
        self.createUser(const.CTYPE_DATACLERK, "666777")
        self.createUser(const.CTYPE_TRIAGENURSE, "666888")
        self.assertEqual(0, Referral.objects.count())
        
    def testRefer(self):
        success_resp = const.REFERRAL_RESPONSE % {"name": self.name, 
                                                  "unique_id": "1234"}
        notif = const.REFERRAL_NOTIFICATION % {"unique_id": "1234"}
        script = """
            %(num)s > refer 1234 804024 hbp 1200 nem
            %(num)s < %(resp)s
            %(danum)s < %(notif)s
            %(tnnum)s < %(notif)s
        """ % {"num": self.user_number, "resp": success_resp, 
               "danum": "666777", "tnnum": "666888", "notif": notif}
        self.runScript(script)
        
        [referral] = Referral.objects.all()
        self.assertEqual("1234", referral.mother_uid)
        self.assertEqual(Location.objects.get(slug__iexact="804024"), referral.facility)
        self.assertTrue(referral.reason_hbp)
        self.assertEqual(["hbp"], list(referral.get_reasons()))
        self.assertEqual("nem", referral.status)
    
    def testMultipleResponses(self):
        success_resp = const.REFERRAL_RESPONSE % {"name": self.name, 
                                                  "unique_id": "1234"}
        notif = const.REFERRAL_NOTIFICATION % {"unique_id": "1234"}
        script = """
            %(num)s > refer 1234 804024 hbp,fd,pec,ec 1200 nem
            %(num)s < %(resp)s
            %(danum)s < %(notif)s
            %(tnnum)s < %(notif)s
        """ % {"num": self.user_number, "resp": success_resp, 
               "danum": "666777", "tnnum": "666888", "notif": notif}
        self.runScript(script)
        
        [referral] = Referral.objects.all()
        self.assertEqual("1234", referral.mother_uid)
        self.assertEqual(Location.objects.get(slug__iexact="804024"), referral.facility)
        self.assertTrue(referral.reason_hbp)
        reasons = list(referral.get_reasons())
        self.assertEqual(4, len(reasons))
        for r in "hbp,fd,pec,ec".split(","):
            self.assertTrue(referral.get_reason(r))
        self.assertEqual("nem", referral.status)
    
      
    def testReferBadLocation(self):
        # bad code
        bad_code_resp = FACILITY_NOT_RECOGNIZED % { "facility": "notaplace" }
        script = """
            %(num)s > refer 1234 notaplace hbp 1200 nem
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": bad_code_resp }
        self.runScript(script)
        
        self.assertEqual(0, Referral.objects.count())
        
    def testReferralOutcome(self):
        resp = const.REFERRAL_OUTCOME_RESPONSE % {"name": self.name,
                                                  "unique_id": "1234" }
        script = """
            %(num)s > refout 1234 stb stb vag
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": resp }
        self.runScript(script)
        
    