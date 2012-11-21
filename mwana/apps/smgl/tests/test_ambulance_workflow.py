import logging

from rapidsms.models import Contact

from mwana.apps.smgl.app import (ER_TO_TRIAGE_NURSE, ER_TO_DRIVER,
    ER_STATUS_UPDATE, AMB_OUTCOME_FILED, AMB_OUTCOME_ORIGINATING_LOCATION_INFO,
    AMB_RESPONSE_ORIGINATING_LOCATION_INFO, AMB_RESPONSE_NOT_AVAILABLE)

from mwana.apps.smgl.tests.shared import SMGLSetUp, create_prereg_user
from mwana.apps.smgl.models import (AmbulanceRequest, AmbulanceResponse,
    AmbulanceOutcome)
from mwana.apps.smgl import const

logging = logging.getLogger(__name__)


class SMGLAmbulanceTest(SMGLSetUp):
    def setUp(self):
        # this call is required if you want to override setUp
        super(SMGLSetUp, self).setUp()
        AmbulanceRequest.objects.all().delete()
        AmbulanceResponse.objects.all().delete()
        AmbulanceOutcome.objects.all().delete()
        create_prereg_user("AntonTN", "804002", '11', 'TN', 'en')
        create_prereg_user("AntonAD", "804002", '12', 'AM', 'en')
        create_prereg_user("AntonDA", "804024", "15", const.CTYPE_DATACLERK, 'en')
        create_prereg_user("AntonSU", "804002", "16", const.CTYPE_DATACLERK, 'en')

        create_users = """
            11 > Join AntonTN EN
            11 < Thank you for registering! You have successfully registered as a Triage Nurse at Kalomo District Hospital.
            12 > join ANTONAmb en
            12 < Thank you for registering! You have successfully registered as a Ambulance at Kalomo District Hospital.
            15 > join AntonDA en
            15 < Thank you for registering! You have successfully registered as a Data Clerk at Chilala.
            16 > join AntonSU en
            16 < Thank you for registering! You have successfully registered as a Data Clerk at Kalomo District Hospital.
        """
        self.runScript(create_users)

    def testAmbRequestWorkflow(self):
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
        """.format(ER_TO_TRIAGE_NURSE % d,
                   ER_TO_DRIVER % d,)
        self.runScript(script)
        [amb_req] = AmbulanceRequest.objects.all()
        self.assertEqual("1234", amb_req.mother_uid)
        self.assertEqual("1", amb_req.danger_sign)
        self.assertEqual("15", amb_req.contact.default_connection.identity)
        self.assertEqual("12", amb_req.ambulance_driver.default_connection.identity)
        self.assertEqual("11", amb_req.triage_nurse.default_connection.identity)
        self.assertEqual(False, amb_req.received_response)

        # response
        self.assertEqual(0, AmbulanceResponse.objects.count())
        d = {
            "unique_id": '1234',
            "status": "OTW",
            "confirm_type": "Triage Nurse",
            "name": "AntonTN",
        }
        response_string = ER_STATUS_UPDATE % d
        d['response'] = 'OTW'
        response_to_referrer_string = AMB_RESPONSE_ORIGINATING_LOCATION_INFO % d
        script = """
            11 > resp 1234 otw
            11 < {0}
            12 < {0}
            15 < {1}
        """.format(response_string, response_to_referrer_string)

        self.runScript(script)
        [amb_req] = AmbulanceRequest.objects.all()
        self.assertEqual(True, amb_req.received_response)
        [amb_resp] = AmbulanceResponse.objects.all()
        self.assertEqual(amb_req, amb_resp.ambulance_request)
        self.assertEqual("1234", amb_resp.mother_uid)
        self.assertEqual("otw", amb_resp.response)
        self.assertEqual("11", amb_resp.responder.default_connection.identity)

        # outcome
        self.assertEqual(0, AmbulanceOutcome.objects.count())
        d["contact_type"] = "Triage Nurse"
        outcome_string = AMB_OUTCOME_FILED % d
        d['outcome'] = 'under-care'
        outcome_to_referrer_string = AMB_OUTCOME_ORIGINATING_LOCATION_INFO % d
        script = """
            11 > outc 1234 under-care
            11 < {0}
            12 < {0}
            15 < {1}
        """.format(outcome_string, outcome_to_referrer_string)

        self.runScript(script)
        [amb_outcome] = AmbulanceOutcome.objects.all()
        self.assertEqual(amb_req, amb_outcome.ambulance_request)
        self.assertEqual("1234", amb_outcome.mother_uid)
        self.assertEqual("under-care", amb_outcome.outcome)

    def testAmbRequestNAWorkflow(self):
        self.assertEqual(0, AmbulanceRequest.objects.count())
        # assign superuser
        su = Contact.objects.get(name="AntonSU")
        su.is_super_user = True
        su.save()
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
        """.format(ER_TO_TRIAGE_NURSE % d,
                   ER_TO_DRIVER % d,)
        self.runScript(script)
        [amb_req] = AmbulanceRequest.objects.all()
        self.assertEqual("1234", amb_req.mother_uid)
        self.assertEqual("1", amb_req.danger_sign)
        self.assertEqual("15", amb_req.contact.default_connection.identity)
        self.assertEqual("12", amb_req.ambulance_driver.default_connection.identity)
        self.assertEqual("11", amb_req.triage_nurse.default_connection.identity)
        self.assertEqual(False, amb_req.received_response)

        # response
        self.assertEqual(0, AmbulanceResponse.objects.count())
        d = {
            "unique_id": '1234',
            "status": "NA",
            "confirm_type": "Triage Nurse",
            "name": "AntonTN",
            "from_location": 'Chilala',
            "sender_phone_number": '15'
        }
        response_string = ER_STATUS_UPDATE % d
        d['response'] = 'NA'
        response_to_referrer_string = AMB_RESPONSE_ORIGINATING_LOCATION_INFO % d
        amb_na_string = AMB_RESPONSE_NOT_AVAILABLE % d
        script = """
            11 > resp 1234 na
            11 < {0}
            12 < {0}
            15 < {1}
            16 < {2}
        """.format(response_string, response_to_referrer_string, amb_na_string)

        self.runScript(script)
        [amb_req] = AmbulanceRequest.objects.all()
        self.assertEqual(True, amb_req.received_response)
        [amb_resp] = AmbulanceResponse.objects.all()
        self.assertEqual(amb_req, amb_resp.ambulance_request)
        self.assertEqual("1234", amb_resp.mother_uid)
        self.assertEqual("na", amb_resp.response)
        self.assertEqual("11", amb_resp.responder.default_connection.identity)
