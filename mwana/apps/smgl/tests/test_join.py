from mwana.apps.smgl.tests.shared import SMGLSetUp, create_prereg_user
from mwana.apps.smgl.app import USER_SUCCESS_REGISTERED


class SMGLJoinTest(SMGLSetUp):
    fixtures = ["initial_data.json"]

    def testCreateUser(self):
        create_prereg_user("Anton", "804024", "11", "TN", "en")
        script = """
            11 > join Anton en
            11 < %s

        """ % (USER_SUCCESS_REGISTERED % {"name": "Anton",
                                          "readable_user_type": "Triage Nurse",
                                          "facility": "Chilala"})  # TODO:Is this bad testing style?
        self.runScript(script)

        script = """
            11 > join Anton sw
            11 < Anton, you are already registered as a Triage Nurse at Chilala but your details have been updated
        """
        self.runScript(script)

    def testJoin(self):
        self.createDefaults()

    def testNotPreRegd(self):
        script = """
            12 > join Foo en
            12 < Sorry, you are not on the pre-registered users list. Please contact ZCAHRD for assistance
        """
        self.runScript(script)

