from rapidsms.models import Contact
from rapidsms.tests.harness import MockBackend
from threadless_router.router import Router
from threadless_router.tests.scripted import TestScript
from mwana.apps.smgl.app import ER_TO_TRIAGE_NURSE, ER_TO_CLINIC_WORKER, ER_TO_OTHER, ER_TO_DRIVER,\
    ER_STATUS_UPDATE, AMB_OUTCOME_FILED
import logging
from mwana.apps.smgl.tests.shared import SMGLSetUp, create_prereg_user
from mwana.apps.smgl.models import AmbulanceRequest, AmbulanceResponse,\
    AmbulanceOutcome
logging = logging.getLogger(__name__)


class SMGLAmbulanceTest(SMGLSetUp):
    def setUp(self):
        # this call is required if you want to override setUp
        super(SMGLSetUp, self).setUp()
        AmbulanceRequest.objects.all().delete()
        AmbulanceResponse.objects.all().delete()
        AmbulanceOutcome.objects.all().delete()
        create_prereg_user("AntonTN", "kalomo_district", '11', 'TN', 'en')
        create_prereg_user("AntonAD", "804030", '12', 'AM', 'en')
        create_prereg_user("AntonCW", "804030", '13', 'worker', 'en')
        create_prereg_user("AntonOther", "kalomo_district", "14", 'dmho', 'en')
        create_prereg_user("AntonDA", "804024", "15", "DA", 'en')

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
        self.assertEqual(0, AmbulanceRequest.objects.count())
        # request
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
        
        self.runScript(script)
        [amb_req] = AmbulanceRequest.objects.all()
        self.assertEqual("1234", amb_req.mother_uid)
        self.assertEqual("1", amb_req.danger_sign)
        self.assertEqual("15", amb_req.contact.default_connection.identity)
        self.assertEqual("12", amb_req.ambulance_driver.default_connection.identity)
        self.assertEqual("11", amb_req.triage_nurse.default_connection.identity)
        self.assertEqual("14", amb_req.other_recipient.default_connection.identity)
        self.assertEqual(False, amb_req.received_response)
        
        # response
        self.assertEqual(0, AmbulanceResponse.objects.count())
        d = {
            "unique_id": '1234',
            "status" : "CONFIRMED",
            "confirm_type": "Triage Nurse",
            "name": "AntonTN",
        }
        response_string = ER_STATUS_UPDATE  % d
        script = """
            11 > resp 1234 confirmed
            11 < {0}
            12 < {0}
            13 < {0}
            14 < {0}
            # NOTE: is the message also supposed to go to this person? (DA)
            # 15 < {0}
        """.format(response_string)

        self.runScript(script)
        [amb_req] = AmbulanceRequest.objects.all()
        self.assertEqual(True, amb_req.received_response)
        [amb_resp] = AmbulanceResponse.objects.all()
        self.assertEqual(amb_req, amb_resp.ambulance_request)
        self.assertEqual("1234", amb_resp.mother_uid)
        self.assertEqual("confirmed", amb_resp.response)
        self.assertEqual("11", amb_resp.responder.default_connection.identity)
        
        # outcome
        self.assertEqual(0, AmbulanceOutcome.objects.count())
        d["contact_type"] = "Triage Nurse"
        outcome_string = AMB_OUTCOME_FILED  % d
        script = """
            11 > outc 1234 under-care
            11 < {0}
            12 < {0}
            13 < {0}
            14 < {0}
            # NOTE: is the message also supposed to go to this person? (DA)
            # 15 < {0}
        """.format(outcome_string)
        
        self.runScript(script)
        [amb_outcome] = AmbulanceOutcome.objects.all()
        self.assertEqual(amb_req, amb_outcome.ambulance_request)
        self.assertEqual("1234", amb_outcome.mother_uid)
        self.assertEqual("under-care", amb_outcome.outcome)
        
        
