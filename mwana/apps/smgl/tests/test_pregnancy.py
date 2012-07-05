from mwana.apps.smgl.tests.shared import SMGLSetUp 
from mwana.apps.smgl.models import PregnantMother, FacilityVisit
from mwana.apps.smgl import const
from datetime import date, datetime


class SMGLPregnancyTest(SMGLSetUp):
    fixtures = ["initial_data.json"]
    
    def setUp(self):
        super(SMGLPregnancyTest, self).setUp()
        self.createDefaults()
        self.user_number = "15"
        self.name = "AntonDA"
        self.assertEqual(0, PregnantMother.objects.count())
        self.assertEqual(0, FacilityVisit.objects.count())
        
        
    def testRegister(self):
        resp = const.MOTHER_SUCCESS_REGISTERED % { "name": self.name,
                                                   "unique_id": "80403000000112" }
        script = """
            %(num)s > REG 80403000000112 Mary Soko none 04 08 2012 R 80402404 12 02 2012 18 11 2012
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": resp }
        self.runScript(script)
        
        self.assertEqual(1, PregnantMother.objects.count())
        mom = PregnantMother.objects.get(uid='80403000000112')
        self.assertEqual(self.user_number, mom.contact.default_connection.identity)
        self.assertEqual("Mary", mom.first_name)
        self.assertEqual("Soko", mom.last_name)
        self.assertEqual(date(2012, 2, 12), mom.lmp)
        self.assertEqual(date(2012, 11, 18), mom.edd)
        self.assertEqual(date(2012, 8, 4), mom.next_visit)
        self.assertTrue(mom.risk_reason_none)
        self.assertEqual(["none"], list(mom.get_risk_reasons()))
        self.assertEqual("r", mom.reason_for_visit)
        
        self.assertEqual(1, FacilityVisit.objects.count())
        visit = FacilityVisit.objects.get(mother=mom)
        self.assertEqual(self.user_number, visit.contact.default_connection.identity)
        self.assertEqual("804024", visit.location.slug)
        self.assertEqual("r", visit.reason_for_visit)
        self.assertEqual(date(2012, 11, 18), visit.edd)
        self.assertEqual(date(2012, 8, 4), visit.next_visit)
        
    def testRegisterMultipleReasons(self):
        resp = const.MOTHER_SUCCESS_REGISTERED % { "name": self.name,
                                                   "unique_id": "80403000000112" }
        reasons = "csec,cmp,gd,hbp"
        script = """
            %(num)s > REG 80403000000112 Mary Soko %(reasons)s 04 08 2012 R 80402404 12 02 2012 18 11 2012
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": resp, "reasons": reasons }
        self.runScript(script)
        
        mom = PregnantMother.objects.get(uid='80403000000112')
        rback = list(mom.get_risk_reasons())
        self.assertEqual(4, len(rback))
        for r in reasons.split(","):
            self.assertTrue(r in rback)
            self.assertTrue(mom.get_risk_reason(r))
            self.assertTrue(getattr(mom, "risk_reason_%s" % r))
        
    def testRegisterWithBadZone(self):
        resp = const.UNKOWN_ZONE % { "zone": "notarealzone" }
        script = """
            %(num)s > REG 80403000000112 Mary Soko none 04 08 2012 R notarealzone 12 02 2012 18 11 2012
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": resp }
        self.runScript(script)
        self.assertEqual(0, PregnantMother.objects.count())
        self.assertEqual(0, FacilityVisit.objects.count())
    
    def testLayCounselorNotification(self):
        lay_num = "555666"
        lay_name = "lay_counselor"
        self.createUser(const.CTYPE_LAYCOUNSELOR, lay_num, lay_name, "80402404")
        resp = const.MOTHER_SUCCESS_REGISTERED % {"name": self.name,
                                                  "unique_id": "80403000000112" }
        lay_msg = const.NEW_MOTHER_NOTIFICATION % {"mother": "Mary Soko",
                                                   "unique_id": "80403000000112" }
        script = """
            %(num)s > REG 80403000000112 Mary Soko none 04 08 2012 R 80402404 12 02 2012 18 11 2012
            %(num)s < %(resp)s
            %(lay_num)s < %(lay_msg)s
        """ % { "num": self.user_number, "resp": resp, 
                "lay_num": lay_num, "lay_msg": lay_msg }
        self.runScript(script)
        self.assertEqual(1, PregnantMother.objects.count())
        self.assertEqual(1, FacilityVisit.objects.count())
    
    def testFollowUp(self):
        self.testRegister()
        resp = const.FOLLOW_UP_COMPLETE % { "name": self.name,
                                            "unique_id": "80403000000112" }
        script = """
            %(num)s > FUP 80403000000112 R 18 11 2012 02 12 2012 
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": resp }
        self.runScript(script)
        
        self.assertEqual(1, PregnantMother.objects.count())
        self.assertEqual(2, FacilityVisit.objects.count())
    
    def testTold(self):
        self.testRegister()
        resp = const.TOLD_COMPLETE % { "name": self.name }
        script = """
            %(num)s > told 80403000000112 edd
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": resp }
        self.runScript(script)
        
        
        
    