from mwana.apps.smgl.tests.shared import SMGLSetUp
from mwana.apps.smgl.app import DEATH_REG_RESPONSE


class SMGLDeathRegTest(SMGLSetUp):
    fixtures = ["initial_data.json"]
    
    def setUp(self):
        super(SMGLDeathRegTest, self).setUp()
        self.user_number = "123"
        self.name = "Anton"
        self.createUser("worker", self.user_number)
        
    # TODO: beef these up. Just testing the basic workflow
    def testBasicBirthReg(self):
        resp = DEATH_REG_RESPONSE % {"name": self.name }
        script = """
            %(num)s > death 1234 01 01 2012 1 1 1
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": resp }
        self.runScript(script)
        
        