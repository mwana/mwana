from datetime import date
from datetime import timedelta
from rapidsms.models import Contact
from rapidsms.tests.harness import MockBackend
from threadless_router.router import Router
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from mwana.apps.reminders.models import Event
from mwana.apps.contactsplus.models import ContactType
from threadless_router.tests.scripted import TestScript
from mwana.apps.smgl.app import USER_SUCCESS_REGISTERED, ER_TO_TRIAGE_NURSE, ER_TO_CLINIC_WORKER, ER_TO_OTHER, ER_TO_DRIVER
from mwana.apps.smgl.models import PreRegistration
import logging
logging = logging.getLogger(__name__)

def _create_prereg_user(fname, location_code, ident, ctype, lang=None):
    if not lang:
        lang = "en"
    logging.debug('Creating Prereg Object in DB: ident:%s, contact_type:%s, lang:%s' % (ident, ctype, lang))
    pre = PreRegistration()
    pre.first_name = fname
    pre.facility_code = location_code
    pre.phone_number = ident
    pre.unique_id = ident.strip().strip('+')
    pre.title = ctype
    pre.language=lang
    pre.save()
    return pre



class SMGLSetUp(TestScript):

    def createUser(self, ctype, ident):
        pre_reg = _create_prereg_user("Anton", "403029", ident, ctype, "en")
        script = """
            %s > join Anton
        """ % ident
        self.runScript(script)


    def setUp(self):
        # this call is required if you want to override setUp
        super(SMGLSetUp, self).setUp()
        backends = {'mockbackend': {"ENGINE": MockBackend}}
        router = Router(backends=backends)

class SMGLJoinTest(SMGLSetUp):
    fixtures = ["initial_data.json"]
    def testCreateUser(self):
        pre_reg = _create_prereg_user("Anton", "804024", "11", "TN", "en")
        script = """
            11 > join Anton
            11 < %s

        """ % (USER_SUCCESS_REGISTERED % {"name" : "Anton", "readable_user_type": "Triage Nurse",
                                          "facility": "Chilala"}) #TODO:Is this bad testing style?
        self.runScript(script)

        script = """
            11 > join Anton
            11 < Anton, you are already registered as a Triage Nurse at Chilala but your details have been updated
        """
        self.runScript(script)

    def testJoin(self):
        _create_prereg_user("AntonTN", "kalomo_district", '11', 'TN', 'en')
        _create_prereg_user("AntonAD", "804030", '12', 'AM', 'en')
        _create_prereg_user("AntonCW", "804030", '13', 'worker', 'en')
        _create_prereg_user("AntonOther", "kalomo_district", "14", 'dmho', 'en')
        _create_prereg_user("AntonDA", "804024", "15", "DA", 'en')

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
            12 > join Foo
            12 < Sorry, you are not on the pre-registered users list. Please contact ZCAHRD for assistance
        """
        self.runScript(script)

#    def testCreateUserOtherLang(self):
#        pre_reg = _create_prereg_user("Anton", "chilala", "11", "TN", "en")
#        script = """
#            11 > join Anton TO
#            11 < %s
#
#        """ % (USER_SUCCESS_REGISTERED % {"name" : "Anton", "readable_user_type": "Triage Nurse",
#                                          "facility": "Chilala"}) #TODO:Is this bad testing style?
#        self.runScript(script)
#        c = Contact.objects.get(connection__identity="11")
#        self.assertEqual(c.language, "TO", "Language in Contact object should be set to \"TO\"")



class SMGLAmbulanceTest(SMGLSetUp):
    def setUp(self):
        # this call is required if you want to override setUp
        super(SMGLSetUp, self).setUp()
        _create_prereg_user("AntonTN", "kalomo_district", '11', 'TN', 'en')
        _create_prereg_user("AntonAD", "804030", '12', 'AM', 'en')
        _create_prereg_user("AntonCW", "804030", '13', 'worker', 'en')
        _create_prereg_user("AntonOther", "kalomo_district", "14", 'dmho', 'en')
        _create_prereg_user("AntonDA", "804024", "15", "DA", 'en')

        create_users = """
            11 > Join AntonTN EN
            11 < Thank you for registering! You have successfully registered as a Triage Nurse at Kalomo District.
            12 > join ANTONAmb en
            12 < Thank you for registering! You have successfully registered as a Ambulance at Kalomo District Hospital HAHC.
            13 > join antonCW en
            13 < Thank you for registering! You have successfully registered as a Clinic Worker at Kalomo District Hospital HAHC.
            14 > join antonOther en
            14 < Thank you for registering! You have successfully registered as a District mHealth Officer at Kalomo District.
            15 > join AntonDA en
            15 < Thank you for registering! You have successfully registered as a Data Associate at Chilala.
        """
        self.runScript(create_users)

    def testAmbRequest(self):
        d = {
            "unique_id": '1234',
            "from_location": 'Chilala',
            "sender_phone_number": '15'
        }
        script = """
            15 > AMB 1234 1
            15 < Thank you.Your request for an ambulance has been received. Someone will be in touch with you shortly.If no one contacts you,please call the emergency number!
            11 < {0}
            12 < {1}
            13 < {2}
            14 < {3}
        """.format(ER_TO_TRIAGE_NURSE % d,
            ER_TO_DRIVER % d,
            ER_TO_CLINIC_WORKER % d,
            ER_TO_OTHER % d)


        d = {
            "unique_id": '1234',
            "status" : "CONFIRMED",
            "confirm_type": "Triage Nurse",
            "name": "AntonTN",
        }
        response_string = "The Emergency Request for Mother with Unique ID: " \
                          "%(unique_id)s has been marked %(status)s by %(name)s " \
                          "(%(confirm_type)s)" % d
        script += """
            11 > resp 1234 confirmed
            11 < {0}
            12 < {0}
            13 < {0}
            14 < {0}
            15 < {0}
        """.format(response_string)

        self.runScript(script)
