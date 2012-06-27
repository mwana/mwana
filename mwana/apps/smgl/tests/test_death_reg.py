from mwana.apps.smgl.tests.shared import SMGLSetUp
from mwana.apps.smgl.app import DEATH_REG_RESPONSE
from mwana.apps.smgl.models import DeathRegistration
from datetime import date

class SMGLDeathRegTest(SMGLSetUp):
    fixtures = ["initial_data.json"]
    
    def setUp(self):
        super(SMGLDeathRegTest, self).setUp()
        self.user_number = "123"
        self.name = "Anton"
        self.createUser("worker", self.user_number)
        DeathRegistration.objects.all().delete()
        
    # TODO: beef these up. Just testing the basic workflow
    def testBasicDeathReg(self):
        resp = DEATH_REG_RESPONSE % {"name": self.name }
        script = """
            %(num)s > death 1234 01 01 2012 ma h
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": resp }
        self.runScript(script)
        [reg] = DeathRegistration.objects.all()
        self.assertEqual("1234", reg.unique_id)
        self.assertEqual(date(2012, 1, 1), reg.date)
        self.assertEqual("ma", reg.person)
        self.assertEqual("h", reg.place)
        
        