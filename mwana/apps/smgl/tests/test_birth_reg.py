from mwana.apps.smgl.tests.shared import SMGLSetUp
from mwana.apps.smgl.app import BIRTH_REG_RESPONSE


class SMGLBirthRegTest(SMGLSetUp):
    fixtures = ["initial_data.json"]
    
    def setUp(self):
        super(SMGLBirthRegTest, self).setUp()
        self.user_number = "123"
        self.name = "Anton"
        self.createUser("worker", self.user_number)
    
    # TODO: beef these up. Just testing the basic workflow
    def testBasicDeathReg(self):
        resp = BIRTH_REG_RESPONSE % {"name": self.name }
        script = """
            %(num)s > birth 1234 01 01 2012 1 1
            %(num)s < %(resp)s            
        """ % { "num": self.user_number, "resp": resp }
        self.runScript(script)
        
        