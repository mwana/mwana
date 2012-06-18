from mwana.apps.smgl.tests.shared import SMGLSetUp, create_prereg_user
from mwana.apps.smgl.app import USER_SUCCESS_REGISTERED


class SMGLJoinTest(SMGLSetUp):
    fixtures = ["initial_data.json"]
    def testCreateUser(self):
        create_prereg_user("Anton", "804024", "11", "TN", "en")
        script = """
            11 > join Anton en
            11 < %s

        """ % (USER_SUCCESS_REGISTERED % {"name" : "Anton", "readable_user_type": "Triage Nurse",
                                          "facility": "Chilala"}) #TODO:Is this bad testing style?
        self.runScript(script)

        script = """
            11 > join Anton en
            11 < Anton, you are already registered as a Triage Nurse at Chilala but your details have been updated
        """
        self.runScript(script)

    def testJoin(self):
        create_prereg_user("AntonTN", "kalomo_district", '11', 'TN', 'en')
        create_prereg_user("AntonAD", "804030", '12', 'AM', 'en')
        create_prereg_user("AntonCW", "804030", '13', 'worker', 'en')
        create_prereg_user("AntonOther", "kalomo_district", "14", 'dmho', 'en')
        create_prereg_user("AntonDA", "804024", "15", "DA", 'en')

        create_users = """
            11 > Join AntonTN EN
            11 < Thank you for registering! You have successfully registered as a Triage Nurse at Kalomo District.
            12 > join ANTONAD en
            12 < Thank you for registering! You have successfully registered as a Ambulance at Kalomo District Hospital HAHC.
            13 > join antonCW en
            13 < Thank you for registering! You have successfully registered as a Clinic Worker at Kalomo District Hospital HAHC.
            14 > join antonOther en
            14 < Thank you for registering! You have successfully registered as a District mHealth Officer at Kalomo District.
            15 > join AntonAD en
            15 < Thank you for registering! You have successfully registered as a Data Associate at Chilala.
        """
        self.runScript(create_users)

    def testNotPreRegd(self):
        script = """
            12 > join Foo en
            12 < Sorry, you are not on the pre-registered users list. Please contact ZCAHRD for assistance
        """
        self.runScript(script)

