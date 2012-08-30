from mwana.apps.smgl.tests.shared import SMGLSetUp
from mwana.apps.smgl.models import Referral, PregnantMother,\
    ReminderNotification
from mwana.apps.smgl.app import FACILITY_NOT_RECOGNIZED
from mwana.apps.locations.models import Location
from mwana.apps.smgl import const
import datetime
from mwana.apps.smgl.reminders import send_non_emergency_referral_reminders,\
    send_emergency_referral_reminders

def _verbose_reasons(reasonstring):
    return ", ".join([Referral.REFERRAL_REASONS[r] for r in reasonstring.split(", ")])

class SMGLReferTest(SMGLSetUp):
    fixtures = ["initial_data.json"]
    
    def setUp(self):
        super(SMGLReferTest, self).setUp()
        Referral.objects.all().delete()
        ReminderNotification.objects.all().delete()
        self.user_number = "123"
        self.cba_number = "456"
        self.name = "Anton"
        self.createUser("worker", self.user_number, location="804034")
        self.cba = self.createUser("cba", self.cba_number, location="80402404")
        self.dc = self.createUser(const.CTYPE_DATACLERK, "666777")
        self.createUser(const.CTYPE_TRIAGENURSE, "666888")
        self.assertEqual(0, Referral.objects.count())
        
    def testRefer(self):
        success_resp = const.REFERRAL_RESPONSE % {"name": self.name, 
                                                  "unique_id": "1234"}
        notif = const.REFERRAL_NOTIFICATION % {"unique_id": "1234",
                                               "facility": "Mawaya",
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
                                               "facility": "Mawaya",
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
        
    def testReferWithMother(self):
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).date()
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
        resp = const.MOTHER_SUCCESS_REGISTERED % { "name": self.name,
                                                   "unique_id": "1234" }
        script = """
            %(num)s > REG 1234 Mary Soko none %(future)s R 80402404 %(past)s %(future)s
            %(num)s < %(resp)s            
        """ % {"num": "666777", "resp": resp,
               "past": yesterday.strftime("%d %m %Y"), 
               "future": tomorrow.strftime("%d %m %Y")}
        self.runScript(script)
        mom = PregnantMother.objects.get(uid='1234')
        self.testRefer()
        [ref] = Referral.objects.all()
        self.assertEqual(mom.uid, ref.mother_uid)
        self.assertEqual(mom, ref.mother)
    
    def testNonEmergencyReminders(self):
        self.testReferWithMother()
        [ref] = Referral.objects.all()
        self.assertEqual(False, ref.reminded)
        self.assertEqual(1, Referral.non_emergencies().count())
        
        # this should do nothing because it's not in range
        send_non_emergency_referral_reminders()
        ref = Referral.objects.get(pk=ref.pk)
        self.assertEqual(False, ref.reminded)
        
        # set the date back so it triggers a reminder
        ref.date = ref.date - datetime.timedelta(days=7)
        ref.save()
        send_non_emergency_referral_reminders()
        reminder = const.REMINDER_NON_EMERGENCY_REFERRAL % {"name": "Mary Soko",
                                                            "unique_id": "1234",
                                                            "loc": "Chilala"}
        script = """ 
            %(num)s < %(msg)s
        """ % {"num": self.cba_number, 
               "msg": reminder}
        self.runScript(script)
        
        ref = Referral.objects.get(pk=ref.pk)
        self.assertEqual(True, ref.reminded)
        [notif] = ReminderNotification.objects.all()
        self.assertEqual(ref.mother, notif.mother)
        self.assertEqual(ref.mother_uid, notif.mother_uid)
        self.assertEqual(self.cba, notif.recipient)
        self.assertEqual("nem_ref", notif.type)
        
    def testEmergencyReminders(self):
        self.testReferWithMother()
        [ref] = Referral.objects.all()
        ref.status = 'em'
        ref.save()
        self.assertEqual(False, ref.reminded)
        self.assertEqual(1, Referral.emergencies().count())
        
        # this should do nothing because it's not in range
        send_emergency_referral_reminders()
        ref = Referral.objects.get(pk=ref.pk)
        self.assertEqual(False, ref.reminded)
        
        # set the date back so it triggers a reminder
        ref.date = ref.date - datetime.timedelta(days=3)
        ref.save()
        send_emergency_referral_reminders()
        reminder = const.REMINDER_EMERGENCY_REFERRAL % {"unique_id": "1234",
                                                        "date": ref.date.date(),
                                                        "loc": "Mawaya"}
        script = """ 
            %(num)s < %(msg)s
        """ % {"num": "666777", 
               "msg": reminder}
        self.runScript(script)
        
        ref = Referral.objects.get(pk=ref.pk)
        self.assertEqual(True, ref.reminded)
        [notif] = ReminderNotification.objects.all()
        self.assertEqual(ref.mother, notif.mother)
        self.assertEqual(ref.mother_uid, notif.mother_uid)
        self.assertEqual(self.dc, notif.recipient)
        self.assertEqual("em_ref", notif.type)
        