from mwana.apps.smgl.tests.shared import SMGLSetUp
from mwana.apps.smgl.models import Referral
from mwana.apps.smgl.app import FACILITY_NOT_RECOGNIZED
from mwana.apps.locations.models import Location
from mwana.apps.smgl import const
import datetime

def _verbose_reasons(reasonstring):
    return ", ".join([Referral.REFERRAL_REASONS[r] for r in reasonstring.split(", ")])

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
        notif = const.REFERRAL_NOTIFICATION % {"unique_id": "1234",
                                               "facility": "Chilala",
                                               "reason": _verbose_reasons("hbp"),
                                               "time": "12:00"}
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
        self.assertEqual(datetime.time(12, 00), referral.time)
        self.assertFalse(referral.responded)
        self.assertEqual(None, referral.mother_showed)
        
    def testReferNotRegistered(self):
        script = """
            %(num)s > refer 1234 804024 hbp 1200 nem
            %(num)s < %(resp)s
        """ % {"num": "notacontact", "resp": const.NOT_REGISTERED}
        self.runScript(script)
        
    
    def testMultipleResponses(self):
        success_resp = const.REFERRAL_RESPONSE % {"name": self.name, 
                                                  "unique_id": "1234"}
        notif = const.REFERRAL_NOTIFICATION % {"unique_id": "1234",
                                               "facility": "Chilala",
                                               "reason": _verbose_reasons("ec, fd, hbp, pec"),
                                               "time": "12:00"}
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
        
    def testReferBadCode(self):
        # bad code
        bad_code_resp = 'Answer must be one of the choices for "Reason for referral, choices: fd, pec, ec, hbp, pph, aph, pl, cpd, oth"'
        script = """
            %(num)s > refer 1234 804024 foo 1200 nem
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": bad_code_resp }
        self.runScript(script)
        
        self.assertEqual(0, Referral.objects.count())
    
      
    def testReferBadLocation(self):
        # bad code
        bad_code_resp = FACILITY_NOT_RECOGNIZED % { "facility": "notaplace" }
        script = """
            %(num)s > refer 1234 notaplace hbp 1200 nem
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": bad_code_resp }
        self.runScript(script)
        
        self.assertEqual(0, Referral.objects.count())
        
    def testReferBadTimes(self):
        for bad_time in ["foo", "123", "55555"]:
            resp = const.TIME_INCORRECTLY_FORMATTED % {"time": bad_time}
            script = """
                %(num)s > refer 1234 804024 hbp %(time)s nem
                %(num)s < %(resp)s            
            """ % { "num": self.user_number, "time": bad_time, "resp": resp }
            self.runScript(script)
            self.assertEqual(0, Referral.objects.count())
        
        
    def testReferralOutcome(self):
        self.testRefer()
        resp = const.REFERRAL_OUTCOME_RESPONSE % {"name": self.name,
                                                  "unique_id": "1234" }
        script = """
            %(num)s > refout 1234 stb cri vag
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": resp }
        self.runScript(script)
        [ref] = Referral.objects.all()
        self.assertTrue(ref.responded)
        self.assertTrue(ref.mother_showed)
        self.assertEqual("stb", ref.mother_outcome)
        self.assertEqual("cri", ref.baby_outcome)
        self.assertEqual("vag", ref.mode_of_delivery)
        
    def testReferralOutcomeNoShow(self):
        self.testRefer()
        resp = const.REFERRAL_OUTCOME_RESPONSE % {"name": self.name,
                                                  "unique_id": "1234" }
        script = """
            %(num)s > refout 1234 noshow
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": resp }
        self.runScript(script)
        [ref] = Referral.objects.all()
        self.assertTrue(ref.responded)
        self.assertFalse(ref.mother_showed)
        
    def testReferralOutcomeNoRef(self):
        resp = const.REFERRAL_NOT_FOUND % {"unique_id": "1234" }
        script = """
            %(num)s > refout 1234 stb stb vag
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": resp }
        self.runScript(script)
        
    