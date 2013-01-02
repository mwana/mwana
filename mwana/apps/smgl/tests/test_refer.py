from mwana.apps.smgl.tests.shared import SMGLSetUp
from mwana.apps.smgl.models import (Referral, PregnantMother,
    ReminderNotification, AmbulanceRequest, AmbulanceResponse)
from mwana.apps.smgl.app import FACILITY_NOT_RECOGNIZED
from mwana.apps.locations.models import Location
from mwana.apps.smgl import const
import datetime
from mwana.apps.smgl.reminders import (send_non_emergency_referral_reminders,
    send_emergency_referral_reminders)

from mwana.apps.smgl.app import (ER_TO_TRIAGE_NURSE, ER_TO_DRIVER,
    ER_STATUS_UPDATE, AMB_RESPONSE_ORIGINATING_LOCATION_INFO,
    AMB_RESPONSE_NOT_AVAILABLE, ER_TO_CLINIC_WORKER, INITIAL_AMBULANCE_RESPONSE)


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
        self.cworker = self.createUser("worker", "666444")
        self.cba = self.createUser("cba", self.cba_number, location="80402404")
        self.dc = self.createUser(const.CTYPE_DATACLERK, "666777")
        self.tn = self.createUser(const.CTYPE_TRIAGENURSE, "666888")
        self.am = self.createUser("AM", "666555")
        self.ha = self.createUser("worker", "666111")
        self.ha.is_help_admin = True
        self.ha.save()

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
        self.assertSessionSuccess()

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
        self.assertSessionFail()

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
        self.assertSessionSuccess()

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
        bad_code_resp = 'Answer must be one of the choices for "Reason for referral, choices: fd, pec, ec, hbp, pph, aph, pl, cpd, oth, pp"'
        script = """
            %(num)s > refer 1234 804024 foo 1200 nem
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": bad_code_resp}
        self.runScript(script)
        self.assertSessionFail() # this is a real error that needs fixing
        self.assertEqual(0, Referral.objects.count())

    def testReferBadLocation(self):
        # bad code
        bad_code_resp = FACILITY_NOT_RECOGNIZED % {"facility": "notaplace"}
        script = """
            %(num)s > refer 1234 notaplace hbp 1200 nem
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": bad_code_resp}
        self.runScript(script)
        self.assertSessionFail()
        self.assertEqual(0, Referral.objects.count())

    def testReferBadTimes(self):
        for bad_time in ["foo", "123", "55555"]:
            resp = const.TIME_INCORRECTLY_FORMATTED % {"time": bad_time}
            script = """
                %(num)s > refer 1234 804024 hbp %(time)s nem
                %(num)s < %(resp)s
            """ % {"num": self.user_number, "time": bad_time, "resp": resp}
            self.runScript(script)
            self.assertSessionFail()
            self.assertEqual(0, Referral.objects.count())

    def testReferralOutcome(self):
        self.testRefer()
        resp = const.REFERRAL_OUTCOME_RESPONSE % {"name": self.name,
                                                  "unique_id": "1234"}
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
        self.assertSessionSuccess()
        [ref] = Referral.objects.all()
        self.assertTrue(ref.responded)
        self.assertTrue(ref.mother_showed)
        self.assertEqual("stb", ref.mother_outcome)
        self.assertEqual("cri", ref.baby_outcome)
        self.assertEqual("vag", ref.mode_of_delivery)

    def testReferralOutcomeNoShow(self):
        self.testRefer()
        resp = const.REFERRAL_OUTCOME_RESPONSE % {"name": self.name,
                                                  "unique_id": "1234"}
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
        """ % {"num": self.user_number, "resp": resp, "notify": notify,
                "dc_num": "666999", "ic_num": "666000"}
        self.runScript(script)
        self.assertSessionSuccess()
        [ref] = Referral.objects.all()
        self.assertTrue(ref.responded)
        self.assertFalse(ref.mother_showed)

    def testReferralOutcomeNoRef(self):
        resp = const.REFERRAL_NOT_FOUND % {"unique_id": "1234"}
        script = """
            %(num)s > refout 1234 stb stb vag
            %(num)s < %(resp)s

        """ % {"num": self.user_number, "resp": resp}
        self.runScript(script)
        self.assertSessionFail()

    def testReferWithMother(self):
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).date()
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
        resp = const.MOTHER_SUCCESS_REGISTERED % {"name": self.name,
                                                   "unique_id": "1234"}
        script = """
            %(num)s > REG 1234 Mary Soko none %(future)s R 80402404 %(past)s %(future)s
            %(num)s < %(resp)s
        """ % {"num": "666777", "resp": resp,
               "past": yesterday.strftime("%d %m %Y"),
               "future": tomorrow.strftime("%d %m %Y")}
        self.runScript(script)
        self.assertSessionSuccess()
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

    def testReferEmWorkflow(self):
        d = {
            "unique_id": '1234',
            "from_location": 'Mawaya',
            "sender_phone_number": self.user_number
        }
        script = """
            %(num)s > refer 1234 804024 hbp 1200 em
            %(num)s < %(resp)s
            %(tnnum)s < %(tn_notif)s
            %(amnum)s < %(am_notif)s
        """ % {"num": self.user_number, "amnum": "666555", "tnnum": "666888",
               "resp": INITIAL_AMBULANCE_RESPONSE,
               "tn_notif": ER_TO_TRIAGE_NURSE % d,
               "am_notif": ER_TO_DRIVER % d}
        self.runScript(script)
        self.assertSessionSuccess()

        [referral] = Referral.objects.all()
        self.assertEqual("1234", referral.mother_uid)
        self.assertEqual(Location.objects.get(slug__iexact="804024"), referral.facility)
        self.assertEqual(Location.objects.get(slug__iexact="804034"), referral.from_facility)
        self.assertTrue(referral.reason_hbp)
        self.assertEqual(["hbp"], list(referral.get_reasons()))
        self.assertEqual("em", referral.status)
        self.assertEqual(datetime.time(12, 00), referral.time)
        self.assertFalse(referral.responded)
        self.assertEqual(None, referral.mother_showed)

        [amb_req] = AmbulanceRequest.objects.all()
        self.assertEqual("1234", amb_req.mother_uid)
        self.assertEqual("666555", amb_req.ambulance_driver.default_connection.identity)
        self.assertEqual("666888", amb_req.triage_nurse.default_connection.identity)

        # Test OTW Response
        self.assertEqual(0, AmbulanceResponse.objects.count())
        d = {
            "unique_id": '1234',
            "status": "OTW",
            "confirm_type": "Triage Nurse",
            "name": "Anton",
       }

        response_string = ER_STATUS_UPDATE % d
        d['response'] = 'OTW'
        response_to_worker_string = ER_TO_CLINIC_WORKER % d
        response_to_referrer_string = AMB_RESPONSE_ORIGINATING_LOCATION_INFO % d

        script = """
            %(tnnum)s > resp 1234 otw
            %(tnnum)s < %(resp)s
            %(amnum)s < %(resp)s
            %(wonum)s < %(wo_notif)s
            %(num)s < %(notif)s
        """ % {"num": self.user_number, "amnum": "666555", "tnnum": "666888",
               "wonum": "666444",
               "resp": response_string,
               "wo_notif": response_to_worker_string,
               "notif": response_to_referrer_string}

        self.runScript(script)
        self.assertSessionSuccess()
        [amb_req] = AmbulanceRequest.objects.all()
        self.assertEqual(True, referral.responded)
        [amb_resp] = AmbulanceResponse.objects.all()
        self.assertEqual(amb_req, amb_resp.ambulance_request)
        self.assertEqual("1234", amb_resp.mother_uid)
        self.assertEqual("otw", amb_resp.response)
        self.assertEqual("666888", amb_resp.responder.default_connection.identity)

    def testReferEmNotAvailableWorkflow(self):
        d = {
            "unique_id": '1234',
            "from_location": 'Mawaya',
            "sender_phone_number": self.user_number
        }
        script = """
            %(num)s > refer 1234 804024 hbp 1200 em
            %(num)s < %(resp)s
            %(tnnum)s < %(tn_notif)s
            %(amnum)s < %(am_notif)s
        """ % {"num": self.user_number, "amnum": "666555", "tnnum": "666888",
               "resp": INITIAL_AMBULANCE_RESPONSE,
               "tn_notif": ER_TO_TRIAGE_NURSE % d,
               "am_notif": ER_TO_DRIVER % d}
        self.runScript(script)
        self.assertSessionSuccess()

        [referral] = Referral.objects.all()
        self.assertEqual("1234", referral.mother_uid)
        self.assertEqual(Location.objects.get(slug__iexact="804024"), referral.facility)
        self.assertEqual(Location.objects.get(slug__iexact="804034"), referral.from_facility)
        self.assertTrue(referral.reason_hbp)
        self.assertEqual(["hbp"], list(referral.get_reasons()))
        self.assertEqual("em", referral.status)
        self.assertEqual(datetime.time(12, 00), referral.time)
        self.assertFalse(referral.responded)
        self.assertEqual(None, referral.mother_showed)

        [amb_req] = AmbulanceRequest.objects.all()
        self.assertEqual("1234", amb_req.mother_uid)
        self.assertEqual("666555", amb_req.ambulance_driver.default_connection.identity)
        self.assertEqual("666888", amb_req.triage_nurse.default_connection.identity)

        # Test NA Response
        self.assertEqual(0, AmbulanceResponse.objects.count())
        d = {
            "unique_id": '1234',
            "status": "NA",
            "confirm_type": "Triage Nurse",
            "name": "Anton",
            "from_location": 'Mawaya',
            "sender_phone_number": self.user_number
       }

        response_string = ER_STATUS_UPDATE % d
        d['response'] = 'NA'
        response_to_referrer_string = AMB_RESPONSE_ORIGINATING_LOCATION_INFO % d
        amb_na_string = AMB_RESPONSE_NOT_AVAILABLE % d

        script = """
            %(tnnum)s > resp 1234 na
            %(tnnum)s < %(resp)s
            %(amnum)s < %(resp)s
            %(num)s < %(notif)s
            %(sunum)s < %(su_notif)s
        """ % {"num": self.user_number, "amnum": "666555", "tnnum": "666888",
               "sunum": "666111",
               "resp": response_string,
               "su_notif": amb_na_string,
               "notif": response_to_referrer_string}
        self.runScript(script)
        self.assertSessionSuccess()
        [amb_req] = AmbulanceRequest.objects.all()
        self.assertEqual(True, referral.responded)
        [amb_resp] = AmbulanceResponse.objects.all()
        self.assertEqual(amb_req, amb_resp.ambulance_request)
        self.assertEqual("1234", amb_resp.mother_uid)
        self.assertEqual("na", amb_resp.response)
        self.assertEqual("666888", amb_resp.responder.default_connection.identity)

