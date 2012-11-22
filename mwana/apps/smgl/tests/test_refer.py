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
        self.refferring_dc = self.createUser(const.CTYPE_DATACLERK, "666999",
                                             location="804034")
        self.refferring_ic = self.createUser(const.CTYPE_INCHARGE, "666000",
                                             location="804034")
        self.assertEqual(0, Referral.objects.count())

    def testRefer(self):
        success_resp = const.REFERRAL_RESPONSE % {"name": self.name,
                                                  "unique_id": "1234"}
        notif = const.REFERRAL_NOTIFICATION % {"unique_id": "1234",
                                               "facility": "Mawaya",
                                               "reason": _verbose_reasons("hbp"),
                                               "time": "12:00",
                                               "is_emergency": "no"}
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
        self.assertEqual(Location.objects.get(slug__iexact="804034"), referral.from_facility)
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
                                               "time": "12:00",
                                               "is_emergency": "no"}
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
        notify = const.REFERRAL_OUTCOME_NOTIFICATION % {
            "unique_id": "1234",
            "date": datetime.datetime.now().date(),
            "mother_outcome": "stable",
            "baby_outcome": "critical",
            "delivery_mode": "vaginal"
        }
        script = """
            %(num)s > refout 1234 stb cri vag
            %(num)s < %(resp)s
            %(num)s < %(notify)s
            %(dc_num)s < %(notify)s
            %(ic_num)s < %(notify)s
        """ % {"num": self.user_number, "resp": resp, "notify": notify,
               "dc_num": "666999", "ic_num": "666000"}
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
        notify = const.REFERRAL_OUTCOME_NOTIFICATION_NOSHOW % {
            "unique_id": "1234",
            "date": datetime.datetime.now().date(),
        }
        script = """
            %(num)s > refout 1234 noshow
            %(num)s < %(resp)s
            %(num)s < %(notify)s
            %(dc_num)s < %(notify)s
            %(ic_num)s < %(notify)s
        """ % { "num": self.user_number, "resp": resp, "notify": notify,
                "dc_num": "666999", "ic_num": "666000"}
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

        send_non_emergency_referral_reminders(router_obj=self.router)
        ref = Referral.objects.get(pk=ref.pk)
        self.assertEqual(False, ref.reminded)

        # set the date back so it triggers a reminder
        ref.date = ref.date - datetime.timedelta(days=7)
        ref.save()
        send_non_emergency_referral_reminders(router_obj=self.router)
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
        send_emergency_referral_reminders(router_obj=self.router)
        ref = Referral.objects.get(pk=ref.pk)
        self.assertEqual(False, ref.reminded)

        # set the date back so it triggers a reminder
        ref.date = ref.date - datetime.timedelta(days=3)
        ref.save()
        send_emergency_referral_reminders(router_obj=self.router)
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


#import logging
#
#from rapidsms.models import Contact
#
#from mwana.apps.smgl.app import (ER_TO_TRIAGE_NURSE, ER_TO_DRIVER,
#    ER_STATUS_UPDATE, AMB_OUTCOME_FILED, AMB_OUTCOME_ORIGINATING_LOCATION_INFO,
#    AMB_RESPONSE_ORIGINATING_LOCATION_INFO, AMB_RESPONSE_NOT_AVAILABLE,
#    ER_TO_CLINIC_WORKER)
#
#from mwana.apps.smgl.tests.shared import SMGLSetUp, create_prereg_user
#from mwana.apps.smgl.models import (AmbulanceRequest, AmbulanceResponse,
#    AmbulanceOutcome)
#from mwana.apps.smgl import const
#
#logging = logging.getLogger(__name__)
#
#
#class SMGLAmbulanceTest(SMGLSetUp):
#    def setUp(self):
#        # this call is required if you want to override setUp
#        super(SMGLSetUp, self).setUp()
#        AmbulanceRequest.objects.all().delete()
#        AmbulanceResponse.objects.all().delete()
#        AmbulanceOutcome.objects.all().delete()
#        create_prereg_user("AntonTN", "804002", '11', 'TN', 'en')
#        create_prereg_user("AntonAD", "804002", '12', 'AM', 'en')
#        create_prereg_user("AntonCW", "804002", '13', 'worker', 'en')
#        create_prereg_user("AntonDA", "804024", "15", const.CTYPE_DATACLERK, 'en')
#        create_prereg_user("AntonSU", "804002", "16", const.CTYPE_DATACLERK, 'en')
#
#        create_users = """
#            11 > Join AntonTN EN
#            11 < Thank you for registering! You have successfully registered as a Triage Nurse at Kalomo District Hospital.
#            12 > join ANTONAmb en
#            12 < Thank you for registering! You have successfully registered as a Ambulance at Kalomo District Hospital.
#            13 > join antonCW en
#            13 < Thank you for registering! You have successfully registered as a Clinic Worker at Kalomo District Hospital.
#            15 > join AntonDA en
#            15 < Thank you for registering! You have successfully registered as a Data Clerk at Chilala.
#            16 > join AntonSU en
#            16 < Thank you for registering! You have successfully registered as a Data Clerk at Kalomo District Hospital.
#        """
#        self.runScript(create_users)
#
#    def testAmbRequestWorkflow(self):
#        self.assertEqual(0, AmbulanceRequest.objects.count())
#        # request
#        d = {
#            "unique_id": '1234',
#            "from_location": 'Chilala',
#            "sender_phone_number": '15'
#        }
#        script = """
#            15 > AMB 1234 1
#            15 < Thank you.Your request for an ambulance has been received. Someone will be in touch with you shortly.If no one contacts you,please call the emergency number!
#            11 < {0}
#            12 < {1}
#        """.format(ER_TO_TRIAGE_NURSE % d,
#                   ER_TO_DRIVER % d,)
#        self.runScript(script)
#        [amb_req] = AmbulanceRequest.objects.all()
#        self.assertEqual("1234", amb_req.mother_uid)
#        self.assertEqual("1", amb_req.danger_sign)
#        self.assertEqual("15", amb_req.contact.default_connection.identity)
#        self.assertEqual("12", amb_req.ambulance_driver.default_connection.identity)
#        self.assertEqual("11", amb_req.triage_nurse.default_connection.identity)
#        self.assertEqual(False, amb_req.received_response)
#
#        # response
#        self.assertEqual(0, AmbulanceResponse.objects.count())
#        d = {
#            "unique_id": '1234',
#            "status": "OTW",
#            "confirm_type": "Triage Nurse",
#            "name": "AntonTN",
#        }
#        response_string = ER_STATUS_UPDATE % d
#        d['response'] = 'OTW'
#        response_to_worker_string = ER_TO_CLINIC_WORKER % d
#        response_to_referrer_string = AMB_RESPONSE_ORIGINATING_LOCATION_INFO % d
#        script = """
#            11 > resp 1234 otw
#            11 < {0}
#            12 < {0}
#            13 < {1}
#            15 < {2}
#        """.format(response_string, response_to_worker_string,
#                    response_to_referrer_string)
#
#        self.runScript(script)
#        [amb_req] = AmbulanceRequest.objects.all()
#        self.assertEqual(True, amb_req.received_response)
#        [amb_resp] = AmbulanceResponse.objects.all()
#        self.assertEqual(amb_req, amb_resp.ambulance_request)
#        self.assertEqual("1234", amb_resp.mother_uid)
#        self.assertEqual("otw", amb_resp.response)
#        self.assertEqual("11", amb_resp.responder.default_connection.identity)
#
#        # outcome
#        self.assertEqual(0, AmbulanceOutcome.objects.count())
#        d["contact_type"] = "Triage Nurse"
#        outcome_string = AMB_OUTCOME_FILED % d
#        d['outcome'] = 'under-care'
#        outcome_to_referrer_string = AMB_OUTCOME_ORIGINATING_LOCATION_INFO % d
#        script = """
#            11 > outc 1234 under-care
#            11 < {0}
#            12 < {0}
#            15 < {1}
#        """.format(outcome_string, outcome_to_referrer_string)
#
#        self.runScript(script)
#        [amb_outcome] = AmbulanceOutcome.objects.all()
#        self.assertEqual(amb_req, amb_outcome.ambulance_request)
#        self.assertEqual("1234", amb_outcome.mother_uid)
#        self.assertEqual("under-care", amb_outcome.outcome)
#
#    def testAmbRequestNAWorkflow(self):
#        self.assertEqual(0, AmbulanceRequest.objects.count())
#        # assign superuser
#        su = Contact.objects.get(name="AntonSU")
#        su.is_super_user = True
#        su.save()
#        # request
#        d = {
#            "unique_id": '1234',
#            "from_location": 'Chilala',
#            "sender_phone_number": '15'
#        }
#        script = """
#            15 > AMB 1234 1
#            15 < Thank you.Your request for an ambulance has been received. Someone will be in touch with you shortly.If no one contacts you,please call the emergency number!
#            11 < {0}
#            12 < {1}
#        """.format(ER_TO_TRIAGE_NURSE % d,
#                   ER_TO_DRIVER % d,)
#        self.runScript(script)
#        [amb_req] = AmbulanceRequest.objects.all()
#        self.assertEqual("1234", amb_req.mother_uid)
#        self.assertEqual("1", amb_req.danger_sign)
#        self.assertEqual("15", amb_req.contact.default_connection.identity)
#        self.assertEqual("12", amb_req.ambulance_driver.default_connection.identity)
#        self.assertEqual("11", amb_req.triage_nurse.default_connection.identity)
#        self.assertEqual(False, amb_req.received_response)
#
#        # response
#        self.assertEqual(0, AmbulanceResponse.objects.count())
#        d = {
#            "unique_id": '1234',
#            "status": "NA",
#            "confirm_type": "Triage Nurse",
#            "name": "AntonTN",
#            "from_location": 'Chilala',
#            "sender_phone_number": '15'
#        }
#        response_string = ER_STATUS_UPDATE % d
#        d['response'] = 'NA'
#        response_to_referrer_string = AMB_RESPONSE_ORIGINATING_LOCATION_INFO % d
#        amb_na_string = AMB_RESPONSE_NOT_AVAILABLE % d
#        script = """
#            11 > resp 1234 na
#            11 < {0}
#            12 < {0}
#            15 < {1}
#            16 < {2}
#        """.format(response_string, response_to_referrer_string, amb_na_string)
#
#        self.runScript(script)
#        [amb_req] = AmbulanceRequest.objects.all()
#        self.assertEqual(True, amb_req.received_response)
#        [amb_resp] = AmbulanceResponse.objects.all()
#        self.assertEqual(amb_req, amb_resp.ambulance_request)
#        self.assertEqual("1234", amb_resp.mother_uid)
#        self.assertEqual("na", amb_resp.response)
#        self.assertEqual("11", amb_resp.responder.default_connection.identity)
#
#    def testAmbRequestNoAmbWorkflow(self):
#        self.assertEqual(0, AmbulanceRequest.objects.count())
#        # assign superuser
#        su = Contact.objects.get(name="AntonSU")
#        su.is_super_user = True
#        su.save()
#        # request
#        d = {
#            "unique_id": '1234',
#            "from_location": 'Chilala',
#            "sender_phone_number": '15'
#        }
#        script = """
#            15 > AMB 1234 1
#            15 < Thank you.Your request for an ambulance has been received. Someone will be in touch with you shortly.If no one contacts you,please call the emergency number!
#            11 < {0}
#            12 < {1}
#        """.format(ER_TO_TRIAGE_NURSE % d,
#                   ER_TO_DRIVER % d,)
#        self.runScript(script)
#        [amb_req] = AmbulanceRequest.objects.all()
#        self.assertEqual("1234", amb_req.mother_uid)
#        self.assertEqual("1", amb_req.danger_sign)
#        self.assertEqual("15", amb_req.contact.default_connection.identity)
#        self.assertEqual("12", amb_req.ambulance_driver.default_connection.identity)
#        self.assertEqual("11", amb_req.triage_nurse.default_connection.identity)
#        self.assertEqual(False, amb_req.received_response)
#
#        # response
#        self.assertEqual(0, AmbulanceResponse.objects.count())
#        d = {
#            "unique_id": '1234',
#            "status": "NA",
#            "confirm_type": "Triage Nurse",
#            "name": "AntonTN",
#            "from_location": 'Chilala',
#            "sender_phone_number": '15'
#        }
#        response_string = ER_STATUS_UPDATE % d
#        d['response'] = 'NA'
#        response_to_referrer_string = AMB_RESPONSE_ORIGINATING_LOCATION_INFO % d
#        amb_na_string = AMB_RESPONSE_NOT_AVAILABLE % d
#        script = """
#            11 > resp 1234 na
#            11 < {0}
#            12 < {0}
#            15 < {1}
#            16 < {2}
#        """.format(response_string, response_to_referrer_string, amb_na_string)
#
#        self.runScript(script)
#        [amb_req] = AmbulanceRequest.objects.all()
#        self.assertEqual(True, amb_req.received_response)
#        [amb_resp] = AmbulanceResponse.objects.all()
#        self.assertEqual(amb_req, amb_resp.ambulance_request)
#        self.assertEqual("1234", amb_resp.mother_uid)
#        self.assertEqual("na", amb_resp.response)
#        self.assertEqual("11", amb_resp.responder.default_connection.identity)
#
#        # outcome
#        self.assertEqual(0, AmbulanceOutcome.objects.count())
#        d["contact_type"] = const.CTYPE_DATACLERK
#        d['outcome'] = 'under-care'
#        outcome_to_referrer_string = AMB_OUTCOME_ORIGINATING_LOCATION_INFO % d
#        script = """
#            15 > outc 1234 under-care noamb
#            15 < {0}
#        """.format(outcome_to_referrer_string)
#
#        self.runScript(script)
#        [amb_outcome] = AmbulanceOutcome.objects.all()
#        self.assertEqual(amb_req, amb_outcome.ambulance_request)
#        self.assertEqual(True, amb_outcome.no_amb)
#        self.assertEqual("1234", amb_outcome.mother_uid)
#        self.assertEqual("under-care", amb_outcome.outcome)
#
