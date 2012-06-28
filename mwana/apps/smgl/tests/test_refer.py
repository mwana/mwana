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
        self.createUser(const.CTYPE_DATAASSOCIATE, "666777")
        self.createUser(const.CTYPE_TRIAGENURSE, "666888")
        
    def testRefer(self):
        self.assertEqual(0, Referral.objects.count())
        # bad code
        bad_code_resp = FACILITY_NOT_RECOGNIZED % { "facility": "notaplace" }
        script = """
            %(num)s > refer 1234 notaplace hbp 1200 nem
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": bad_code_resp }
        self.runScript(script)
        
        self.assertEqual(0, Referral.objects.count())
        
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
        
        