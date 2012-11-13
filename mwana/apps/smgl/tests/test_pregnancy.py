from mwana.apps.smgl.tests.shared import SMGLSetUp
from mwana.apps.smgl.models import PregnantMother, FacilityVisit,\
    ReminderNotification, ToldReminder
from mwana.apps.smgl.models import TOLD_TYPE_CHOICES
from mwana.apps.smgl import const
from datetime import datetime, timedelta
from mwana.apps.smgl.reminders import send_followup_reminders,\
    send_upcoming_delivery_reminders
from mwana.apps.smgl.app import BIRTH_REG_RESPONSE
from mwana.apps.smgl.tests.shared import create_birth_registration


class SMGLPregnancyTest(SMGLSetUp):
    fixtures = ["initial_data.json"]

    def setUp(self):
        super(SMGLPregnancyTest, self).setUp()
        ReminderNotification.objects.all().delete()

        self.createDefaults()
        self.user_number = "15"
        self.name = "AntonDA"
        self.cba = self.createUser("cba", "456", location="80402404")

        self.assertEqual(0, PregnantMother.objects.count())
        self.assertEqual(0, FacilityVisit.objects.count())

    def testRegister(self):
        resp = const.MOTHER_SUCCESS_REGISTERED % {"name": self.name,
                                                  "unique_id": "80403000000112"}
        script = """
            %(num)s > REG 80403000000112 Mary Soko none %(tomorrow)s R 80402404 %(earlier)s %(later)s
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp,
               "tomorrow": self.tomorrow.strftime("%d %m %Y"),
               "earlier": self.earlier.strftime("%d %m %Y"),
               "later": self.later.strftime("%d %m %Y")}
        self.runScript(script)

        self.assertEqual(1, PregnantMother.objects.count())
        mom = PregnantMother.objects.get(uid='80403000000112')
        self.assertEqual(self.user_number, mom.contact.default_connection.identity)
        self.assertEqual("Mary", mom.first_name)
        self.assertEqual("Soko", mom.last_name)
        self.assertEqual(self.earlier, mom.lmp)
        self.assertEqual(self.later, mom.edd)
        self.assertEqual(self.tomorrow, mom.next_visit)
        self.assertTrue(mom.risk_reason_none)
        self.assertEqual(["none"], list(mom.get_risk_reasons()))
        self.assertEqual("r", mom.reason_for_visit)

        self.assertEqual(0, FacilityVisit.objects.count())

    def testRegisterNotRegistered(self):
        script = """
            %(num)s > REG 80403000000112 Mary Soko none 04 08 2012 R 80402404 12 02 2012 18 11 2012
            %(num)s < %(resp)s
        """ % {"num": "notacontact", "resp": const.NOT_REGISTERED}
        self.runScript(script)

    def testRegisterMultipleReasons(self):
        resp = const.MOTHER_SUCCESS_REGISTERED % {"name": self.name,
                                                  "unique_id": "80403000000112"}
        reasons = "csec,cmp,gd,hbp"
        script = """
            %(num)s > REG 80403000000112 Mary Soko %(reasons)s %(tomorrow)s R 80402404 %(earlier)s %(later)s
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp, "reasons": reasons,
               "tomorrow": self.tomorrow.strftime("%d %m %Y"),
               "earlier": self.earlier.strftime("%d %m %Y"),
               "later": self.later.strftime("%d %m %Y")}
        self.runScript(script)

        mom = PregnantMother.objects.get(uid='80403000000112')
        rback = list(mom.get_risk_reasons())
        self.assertEqual(4, len(rback))
        for r in reasons.split(","):
            self.assertTrue(r in rback)
            self.assertTrue(mom.get_risk_reason(r))
            self.assertTrue(getattr(mom, "risk_reason_%s" % r))

    def testRegisterWithBadZone(self):
        resp = const.UNKOWN_ZONE % {"zone": "notarealzone"}
        script = """
            %(num)s > REG 80403000000112 Mary Soko none %(tomorrow)s R notarealzone %(earlier)s %(later)s
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp,
               "tomorrow": self.tomorrow.strftime("%d %m %Y"),
               "earlier": self.earlier.strftime("%d %m %Y"),
               "later": self.later.strftime("%d %m %Y")}
        self.runScript(script)
        self.assertEqual(0, PregnantMother.objects.count())
        self.assertEqual(0, FacilityVisit.objects.count())

    def testLayCounselorNotification(self):
        lay_num = "555666"
        lay_name = "lay_counselor"
        self.createUser(const.CTYPE_LAYCOUNSELOR, lay_num, lay_name, "80402404")
        resp = const.MOTHER_SUCCESS_REGISTERED % {"name": self.name,
                                                  "unique_id": "80403000000112"}
        lay_msg = const.NEW_MOTHER_NOTIFICATION % {"mother": "Mary Soko",
                                                   "unique_id": "80403000000112"}
        script = """
            %(num)s > REG 80403000000112 Mary Soko none %(tomorrow)s R 80402404 %(earlier)s %(later)s
            %(num)s < %(resp)s
            %(lay_num)s < %(lay_msg)s
        """ % {"num": self.user_number, "resp": resp,
               "lay_num": lay_num, "lay_msg": lay_msg,
               "tomorrow": self.tomorrow.strftime("%d %m %Y"),
               "earlier": self.earlier.strftime("%d %m %Y"),
               "later": self.later.strftime("%d %m %Y")}
        self.runScript(script)
        self.assertEqual(1, PregnantMother.objects.count())
        self.assertEqual(0, FacilityVisit.objects.count())

    def testDuplicateRegister(self):
        self.testRegister()
        resp = const.DUPLICATE_REGISTRATION % {"unique_id": "80403000000112"}
        script = """
            %(num)s > REG 80403000000112 Mary Someoneelse none %(tomorrow)s R 80402404 %(earlier)s %(later)s
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp,
               "tomorrow": self.tomorrow.strftime("%d %m %Y"),
               "earlier": self.earlier.strftime("%d %m %Y"),
               "later": self.later.strftime("%d %m %Y")}
        self.runScript(script)

        # make sure we didn't create a new one
        self.assertEqual(1, PregnantMother.objects.count())
        mom = PregnantMother.objects.get(uid='80403000000112')
        self.assertEqual("Soko", mom.last_name)

    def testFollowUp(self):
        self.testRegister()
        resp = const.FOLLOW_UP_COMPLETE % {"name": self.name,
                                           "unique_id": "80403000000112"}
        script = """
            %(num)s > FUP 80403000000112 R 18 11 2012 02 12 2012
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp}
        self.runScript(script)

        self.assertEqual(1, PregnantMother.objects.count())
        self.assertEqual(1, FacilityVisit.objects.count())

    def testFollowUpNotRegistered(self):
        script = """
            %(num)s > FUP 80403000000112 R 18 11 2012 02 12 2012
            %(num)s < %(resp)s
        """ % {"num": "notacontact", "resp": const.NOT_REGISTERED}
        self.runScript(script)

    def testFollowUpOptionalEdd(self):
        self.testRegister()
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        resp = const.FOLLOW_UP_COMPLETE % {"name": self.name,
                                           "unique_id": "80403000000112"}
        script = """
            %(num)s > FUP 80403000000112 r %(future)s
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp,
               "future": tomorrow.strftime("%d %m %Y"),
              }
        self.runScript(script)

        self.assertEqual(1, PregnantMother.objects.count())
        self.assertEqual(1, FacilityVisit.objects.count())

    def testFollowUpBadEdd(self):
        self.testRegister()
        resp = const.DATE_INCORRECTLY_FORMATTED_GENERAL % {"date_name": "EDD"}
        script = """
            %(num)s > FUP 80403000000112 r 16 10 2012 not a date
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp}
        self.runScript(script)

        self.assertEqual(1, PregnantMother.objects.count())
        self.assertEqual(0, FacilityVisit.objects.count())

    def testDatesInPastOrFuture(self):
        yesterday = (datetime.now() - timedelta(days=1)).date()
        tomorrow = (datetime.now() + timedelta(days=1)).date()

        # next visit in past
        script = """
            %(num)s > REG 80403000000112 Mary Soko none %(past)s R 80402404 %(past)s %(future)s
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "past": yesterday.strftime("%d %m %Y"),
               "future": tomorrow.strftime("%d %m %Y"),
               "resp": const.DATE_MUST_BE_IN_FUTURE % {"date_name": "Next Visit",
                                                       "date": yesterday}}
        self.runScript(script)

        # lmp in future
        script = """
            %(num)s > REG 80403000000112 Mary Soko none %(future)s R 80402404 %(future)s %(future)s
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "past": yesterday.strftime("%d %m %Y"),
               "future": tomorrow.strftime("%d %m %Y"),
               "resp": const.DATE_MUST_BE_IN_PAST % {"date_name": "LMP",
                                                     "date": yesterday}}
        # edd in past
        script = """
            %(num)s > REG 80403000000112 Mary Soko none %(future)s R 80402404 %(past)s %(past)s
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "past": yesterday.strftime("%d %m %Y"),
               "future": tomorrow.strftime("%d %m %Y"),
               "resp": const.DATE_MUST_BE_IN_FUTURE % {"date_name": "EDD",
                                                       "date": yesterday}}
        self.runScript(script)

    def testValidTold(self):
        self.testRegister()
        [mom] = PregnantMother.objects.all()
        told_reminders = ToldReminder.objects.filter(mother=mom)
        self.assertEqual(0, told_reminders.count())

        resp = const.TOLD_COMPLETE % {"name": self.name}
        for told_type in TOLD_TYPE_CHOICES:
            script = """
                %(num)s > told 80403000000112 %(type)s
                %(num)s < %(resp)s
            """ % {"num": self.user_number, "resp": resp, "type": told_type[0]}
            self.runScript(script)

        told_reminders = ToldReminder.objects.filter(mother=mom)
        self.assertEqual(3, told_reminders.count())

    def testInvalidToldEDD(self):
        self.testRegister()
        [mom] = PregnantMother.objects.all()
        create_birth_registration(data={'mother': mom})

        resp = const.TOLD_MOTHER_HAS_ALREADY_DELIVERED % {"unique_id": mom.uid}
        script = """
            %(num)s > told 80403000000112 EDD
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp}
        self.runScript(script)
        told_reminders = ToldReminder.objects.filter(mother=mom)
        self.assertEqual(0, told_reminders.count())

    def testBadTold(self):
        bad_code_resp = 'Answer must be one of the choices for "Type of reminder, choices: edd, nvd, ref"'
        self.testRegister()
        [mom] = PregnantMother.objects.all()
        told_reminders = ToldReminder.objects.filter(mother=mom)
        self.assertEqual(0, told_reminders.count())

        script = """
            %(num)s > told 80403000000112 invalidcode
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": bad_code_resp}
        self.runScript(script)

        told_reminders = ToldReminder.objects.filter(mother=mom)
        self.assertEqual(0, told_reminders.count())

    def testToldNotRegistered(self):
        script = """
            %(num)s > told 80403000000112 edd
            %(num)s < %(resp)s
        """ % {"num": "notacontact", "resp": const.NOT_REGISTERED}
        self.runScript(script)

    def testVisitReminders(self):
        self.testFollowUp()
        [mom] = PregnantMother.objects.all()
        visit = FacilityVisit.objects.get(mother=mom)
        self.assertEqual(False, visit.reminded)

        # set 10 days in the future, no reminder
        visit.next_visit = datetime.utcnow() + timedelta(days=10)
        visit.save()
        send_followup_reminders(router_obj=self.router)
        visit = FacilityVisit.objects.get(pk=visit.pk)
        self.assertEqual(False, visit.reminded)

        # set to 7 days, should now fall in threshold
        visit.next_visit = datetime.utcnow() + timedelta(days=7)
        visit.save()
        send_followup_reminders(router_obj=self.router)

        reminder = const.REMINDER_FU_DUE % {"name": "Mary Soko",
                                            "unique_id": "80403000000112",
                                            "loc": "Chilala"}
        script = """
            %(num)s < %(msg)s
        """ % {"num": "456",
               "msg": reminder}
        self.runScript(script)

        visit = FacilityVisit.objects.get(pk=visit.pk)
        self.assertEqual(True, visit.reminded)

        [notif] = ReminderNotification.objects.all()
        self.assertEqual(visit.mother, notif.mother)
        self.assertEqual(visit.mother.uid, notif.mother_uid)
        self.assertEqual(self.cba, notif.recipient)
        self.assertEqual("nvd", notif.type)

    def testBirthCancelsVisitReminder(self):
        self.testFollowUp()
        [mom] = PregnantMother.objects.all()
        visit = FacilityVisit.objects.get(mother=mom)
        self.assertEqual(False, visit.reminded)

        # set to 7 days, should fall in threshold
        visit.next_visit = datetime.utcnow() + timedelta(days=7)
        visit.save()

        # but report a birth which should prevent the need
        resp = BIRTH_REG_RESPONSE % {"name": self.name}
        script = """
            %(num)s > birth %(id)s 01 01 2012 bo h yes t2
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "id": mom.uid, "resp": resp}
        self.runScript(script)

        # send reminders and make sure they didn't actually fire on this one
        send_followup_reminders(router_obj=self.router)
        visit = FacilityVisit.objects.get(pk=visit.pk)
        self.assertFalse(visit.reminded)

    def testFollowUpCancelsVisitReminder(self):
        self.testFollowUp()
        [mom] = PregnantMother.objects.all()
        visit = FacilityVisit.objects.get(mother=mom)
        self.assertEqual(False, visit.reminded)

        # set to 7 days, should fall in threshold
        visit.next_visit = datetime.utcnow() + timedelta(days=7)
        visit.save()

        # but report a follow up which should prevent the need
        resp = const.FOLLOW_UP_COMPLETE % {"name": self.name,
                                           "unique_id": "80403000000112"}
        script = """
            %(num)s > FUP 80403000000112 R 19 11 2012 03 12 2012
            %(num)s < %(resp)s
        """ % {"num": self.user_number, "resp": resp}
        self.runScript(script)

        [second_visit] = FacilityVisit.objects.filter(mother=mom).exclude(pk=visit.pk)
        self.assertTrue(second_visit.created_date > visit.created_date)
        # leave this one outside the reminder threshold
        second_visit.next_visit = datetime.utcnow() + timedelta(days=10)
        second_visit.save()

        # send reminders and make sure they didn't actually fire on either one
        send_followup_reminders(router_obj=self.router)
        visit = FacilityVisit.objects.get(pk=visit.pk)
        self.assertFalse(visit.reminded)
        second_visit = FacilityVisit.objects.get(pk=visit.pk)
        self.assertFalse(second_visit.reminded)

    def testEDDReminders(self):
        self.testRegister()
        [mom] = PregnantMother.objects.all()
        self.assertEqual(False, mom.reminded)

        # set 15 days in the future, no reminder
        mom.edd = datetime.utcnow().date() + timedelta(days=15)
        mom.save()
        send_upcoming_delivery_reminders(router_obj=self.router)
        mom = PregnantMother.objects.get(pk=mom.pk)
        self.assertEqual(False, mom.reminded)

        # set to 14 days, should now fall in threshold
        mom.edd = datetime.utcnow().date() + timedelta(days=14)
        mom.save()
        send_upcoming_delivery_reminders(router_obj=self.router)
        mom = PregnantMother.objects.get(pk=mom.pk)
        self.assertEqual(True, mom.reminded)

        reminder = const.REMINDER_UPCOMING_DELIVERY % {"name": "Mary Soko",
                                                       "unique_id": "80403000000112",
                                                       "date": mom.edd}
        script = """
            %(num)s < %(msg)s
        """ % {"num": "456",
               "msg": reminder}
        self.runScript(script)

        [notif] = ReminderNotification.objects.all()
        self.assertEqual(mom, notif.mother)
        self.assertEqual(mom.uid, notif.mother_uid)
        self.assertEqual(self.cba, notif.recipient)
        self.assertEqual("edd_14", notif.type)
