from datetime import datetime, timedelta

from django.db.models import Q, Count

from rapidsms import router
from rapidsms.models import Contact

from threadless_router.router import Router

from mwana.apps.contactsplus.models import ContactType

from mwana.apps.smgl import const
from mwana.apps.smgl.models import FacilityVisit, ReminderNotification, Referral,\
    PregnantMother, AmbulanceResponse, SyphilisTreatment, Location

# reminders will be sent up to this amount late (if, for example the system
# was down.
SEND_REMINDER_LOWER_BOUND = timedelta(days=2)
SEND_AMB_OUTCOME_LOWER_BOUND = timedelta(hours=1)
SEND_SYPHILIS_REMINDER_LOWER_BOUND = timedelta(days=2)


def _set_router(router_obj=None):
    # Set the router to the global router it one is not provided
    if not router_obj:
        router.router = Router()
    else:
        router.router = router_obj


def send_followup_reminders(router_obj=None):
    """
    Next visit date from Pregnancy registration or Follow-up visit should
    be used to generate reminder for the next appointment.

    To: CBA
    On: 7 days before visit date
    """
    _set_router(router_obj)

    def _visits_to_remind():
        now = datetime.utcnow().date()
        reminder_threshold = now + timedelta(days=7)
        visits_to_remind = FacilityVisit.objects.filter(
            next_visit__gte=reminder_threshold - SEND_REMINDER_LOWER_BOUND,
            next_visit__lte=reminder_threshold,
            reminded=False,
            visit_type='anc')

        for v in visits_to_remind:
            if v.mother.birthregistration_set.count() == 0 and \
               v.is_latest_for_mother():
                yield v

    for v in _visits_to_remind():
        found_someone = False
        for c in v.mother.get_laycounselors():
            if c.default_connection:
                found_someone = True
                c.message(const.REMINDER_FU_DUE,
                          **{"name": v.mother.name,
                             "unique_id": v.mother.uid,
                             "loc": v.location.name})
                _create_notification("nvd", c, v.mother.uid)
        if found_someone:
            v.reminded = True
            v.save()


def send_non_emergency_referral_reminders(router_obj=None):
    """
    Reminder for non-emergency referral.

    To: CBA
    On: 7 days after referral is registered in the system

    Reminder is not necessary if mother shows up in the referral center.
    Also If we don't have the mother details (safe motherhood ID, Zone...)
    then the server does nothing.
    """
    _set_router(router_obj)

    now = datetime.utcnow()
    reminder_threshold = now - timedelta(days=7)
    referrals_to_remind = Referral.non_emergencies().filter(
        reminded=False,
        date__gte=reminder_threshold - SEND_REMINDER_LOWER_BOUND,
        date__lte=reminder_threshold
    ).filter(Q(mother_showed=None) | Q(mother_showed=False))
    referrals_to_remind = referrals_to_remind.exclude(mother=None)
    for ref in referrals_to_remind:
        found_someone = False
        for c in ref.mother.get_laycounselors():
            if c.default_connection:
                found_someone = True
                c.message(const.REMINDER_NON_EMERGENCY_REFERRAL,
                          **{"name": ref.mother.name,
                             "unique_id": ref.mother.uid,
                             "loc": ref.facility.name})
                _create_notification("nem_ref", c, ref.mother.uid)
        if found_someone:
            ref.reminded = True
            ref.save()


def send_emergency_referral_reminders(router_obj=None):
    """
    Reminder to collect outcomes for emergency referrals.

    To: Data Clerk operating at the referral facility
    On: 3 days after referral had been entered
    """
    _set_router(router_obj)
    now = datetime.utcnow()
    reminder_threshold = now - timedelta(days=3)
    referrals_to_remind = Referral.emergencies().filter(
        reminded=False,
        responded=False,
        date__gte=reminder_threshold - SEND_REMINDER_LOWER_BOUND,
        date__lte=reminder_threshold
    ).exclude(mother_uid=None)
    for ref in referrals_to_remind:
        found_someone = False
        for c in ref.get_receiving_data_clerks():
            if c.default_connection:
                found_someone = True
                c.message(const.REMINDER_EMERGENCY_REFERRAL,
                          **{"unique_id": ref.mother_uid,
                             "date": ref.date.date(),
                             "loc": ref.referring_facility.name if ref.referring_facility else "?"})
                _create_notification("em_ref", c, ref.mother_uid)
        if found_someone:
            ref.reminded = True
            ref.save()


def send_upcoming_delivery_reminders(router_obj=None):
    """
    Reminders for upcoming delivery

    To: CBA
    On: 14 days prior expected delivery day

    Cancel reminders after notification of birth.
    """
    _set_router(router_obj)
    now = datetime.utcnow().date()
    reminder_threshold = now + timedelta(days=14)
    moms_to_remind = PregnantMother.objects.filter(
        reminded=False,
        birthregistration__isnull=True,
        edd__gte=reminder_threshold - SEND_REMINDER_LOWER_BOUND,
        edd__lte=reminder_threshold
    )
    for mom in moms_to_remind:
        found_someone = False
        for c in mom.get_laycounselors():
            if c.default_connection:
                found_someone = True
                c.message(const.REMINDER_UPCOMING_DELIVERY,
                          **{"name": mom.name,
                             "unique_id": mom.uid,
                             "date": mom.edd})
                _create_notification("edd_14", c, mom.uid)
        if found_someone:
            mom.reminded = True
            mom.save()


def send_first_postpartum_reminders(router_obj=None):
    """
    To: CBA
    On: 3 Days before first postpartum visit
    """
    _set_router(router_obj)

    def _visits_to_remind():
        now = datetime.utcnow().date()
        # Get visits 3 days from now for 1st visit
        reminder_threshold = now + timedelta(days=3)
        visits_to_remind = FacilityVisit.objects.filter(
            next_visit__gte=reminder_threshold - SEND_REMINDER_LOWER_BOUND,
            next_visit__lte=reminder_threshold,
            reminded=False,
            visit_type='pos'
            )
        # Check if first visit for mother

        for v in visits_to_remind:
            if v.mother.facilityvisit_set.filter(visit_type='pos').count() == 0 and \
               v.is_latest_for_mother():
                yield v

    for v in _visits_to_remind():
        found_someone = False
        for c in v.mother.get_laycounselors():
            if c.default_connection:
                found_someone = True
                c.message(const.REMINDER_PP_DUE,
                          **{"name": v.mother.name,
                             "unique_id": v.mother.uid,
                             "loc": v.location.name,
                             "num": 3})
                _create_notification("pos", c, v.mother.uid)
        if found_someone:
            v.reminded = True
            v.save()


def send_second_postpartum_reminders(router_obj=None):
    """
    To: CBA
    On: 7 days before second postpartum visit
    """
    _set_router(router_obj)

    def _visits_to_remind():
        now = datetime.utcnow().date()
        # Get visits 7 days from now for 2nd visit
        reminder_threshold = now + timedelta(days=7)
        visits_to_remind = FacilityVisit.objects.filter(
            next_visit__gte=reminder_threshold - SEND_REMINDER_LOWER_BOUND,
            next_visit__lte=reminder_threshold,
            reminded=False,
            visit_type='pos'
            )
        # Check if second visit

        for v in visits_to_remind:
            if v.mother.facilityvisit_set.filter(visit_type='pos').count() == 1 and \
               v.is_latest_for_mother():
                yield v

    for v in _visits_to_remind():
        found_someone = False
        for c in v.mother.get_laycounselors():
            if c.default_connection:
                found_someone = True
                c.message(const.REMINDER_PP_DUE,
                          **{"name": v.mother.name,
                             "unique_id": v.mother.uid,
                             "loc": v.location.name,
                             "num": 7})
                _create_notification("pos", c, v.mother.uid)
        if found_someone:
            v.reminded = True
            v.save()


def send_missed_postpartum_reminders(router_obj=None):
    """
    To: CBA
    On: 2 Days after a missing postpartum visit
    """
    _set_router(router_obj)

    def _visits_to_remind():
        now = datetime.utcnow().date()
        # Get visits -2 days from now if no POS registered
        reminder_threshold = now - timedelta(days=2)
        visits_to_remind = FacilityVisit.objects.filter(
            next_visit__gte=reminder_threshold - SEND_REMINDER_LOWER_BOUND,
            next_visit__lte=reminder_threshold,
            reminded=False,
            visit_type='pos'
            )
        # Check if missed

        for v in visits_to_remind:
            if v.mother.facilityvisit_set.filter(visit_type='pos',
                                        visit_date=reminder_threshold)\
                        .count() == 1 and \
               v.is_latest_for_mother():
                yield v

    for v in _visits_to_remind():
        found_someone = False
        for c in v.mother.get_laycounselors():
            if c.default_connection:
                found_someone = True
                c.message(const.REMINDER_PP_MISSED,
                          **{"name": v.mother.name,
                             "unique_id": v.mother.uid,
                             "loc": v.location.name})
                _create_notification("pos", c, v.mother.uid)
        if found_someone:
            v.reminded = True
            v.save()


def reactivate_user(router_obj=None):
    """
    Looks up Contacts that are set to is_active=False and have a return date
    of today. Activates user.
    """
    _set_router(router_obj)

    def _contacts_to_activate():
        now = datetime.utcnow().date()

        contacts_to_activate = Contact.objects.filter(
            return_date__gte=now - SEND_REMINDER_LOWER_BOUND,
            return_date__lte=now,
            is_active=False,
            )
        return contacts_to_activate

    for c in _contacts_to_activate():
        if c.default_connection:
            c.return_date = None
            c.is_active = True
            c.save()
            c.message(const.IN_REACTIVATE)


def send_no_outcome_reminder(router_obj=None):
    """
    Send reminders for Amulance Responses that have no Ambulance Outcome
    """
    def _responses_to_remind():
        now = datetime.utcnow().date()
        # Get AmbulanceResponses @ 12 hours old
        reminder_threshold = now - timedelta(hours=12)
        responses_to_remind = AmbulanceResponse.objects.filter(
            responded_on__gte=reminder_threshold - SEND_AMB_OUTCOME_LOWER_BOUND,
            responded_on__lte=reminder_threshold,
            )
        # Check if missed

        for resp in responses_to_remind:
            ref = resp.ambulance_request.referral_set.all()[0]
            if not ref.responded:
                yield resp

    for resp in _responses_to_remind():
        req = resp.ambulance_request
        ref = req.referral_set.all()[0]

        if resp.status == 'na':
            # send reminder to referring facility contact
            contacts = [ref.session.connection.contact]
        else:
            # send reminder(s) to TN and AM
            contacts = [req.ambulance_driver,
                        req.triage_nurse,
                        req.receiving_facility_recipient]

        for c in contacts:
            if c.default_connection:
                c.message(const.AMB_OUTCOME_NO_OUTCOME,
                          **{"unique_id": resp.mother.uid})


def send_no_outcome_help_admin_reminder(router_obj=None):
    """
    Send reminders to help admin for Amulance Responses
    that have no Ambulance Outcome and are @ 24 hours old
    """
    def _responses_to_remind():
        now = datetime.utcnow().date()
        # Get AmbulanceResponses @ 12 hours old
        reminder_threshold = now - timedelta(hours=24)
        responses_to_remind = AmbulanceResponse.objects.filter(
            responded_on__gte=reminder_threshold - SEND_AMB_OUTCOME_LOWER_BOUND,
            responded_on__lte=reminder_threshold,
            )
        # Check if missed

        for resp in responses_to_remind:
            ref = resp.ambulance_request.referral_set.all()[0]
            if not ref.responded:
                yield resp

    for resp in _responses_to_remind():
        req = resp.ambulance_request
        ref = req.referral_set.all()[0]
        receiving_facility = ref.facility
        users = Contact.objects.filter(is_help_admin=True,
                                       location=receiving_facility)
        for u in users:
            if u.default_connection:
                u.message(const.AMB_OUTCOME_NO_OUTCOME,
                          **{"unique_id": resp.mother.uid})


def send_syphillis_reminders(router_obj=None):
    """
    Next visit date from SyphilisTreatment should
    be used to generate reminder for the next appointment.

    To: CBA
    On: 2 days before visit date
    """
    _set_router(router_obj)

    def _visits_to_remind():
        now = datetime.utcnow().date()
        reminder_threshold = now + timedelta(days=2)
        visits_to_remind = SyphilisTreatment.objects.filter(
            next_visit_date__gte=reminder_threshold - SEND_SYPHILIS_REMINDER_LOWER_BOUND,
            next_visit_date__lte=reminder_threshold,
            reminded=False)

        for v in visits_to_remind:
            if v.is_latest_for_mother():
                yield v

    for v in _visits_to_remind():
        found_someone = False
        for c in v.mother.get_laycounselors():
            if c.default_connection:
                found_someone = True
                c.message(const.REMINDER_SYP_TREATMENT_DUE,
                          **{"name": v.mother.name,
                             "unique_id": v.mother.uid,
                             "loc": v.location.name})
                _create_notification("syp", c, v.mother.uid)
        if found_someone:
            v.reminded = True
            v.save()


def send_inactive_notice(router_obj=None):
    """
    Automated Reminder for inactive users

    To: Active CBAs & Data Clerks
    On: 14th day after Contact.latest_sms_date who are marked as
        Contact.is_active=True
    """
    _set_router(router_obj)

    def _contacts_to_remind():
        now = datetime.utcnow().date()
        inactive_threshold = now - timedelta(days=14)
        contacts = Contact.objects.filter(is_active=True)

        for c in contacts:
            last_sent = c.latest_sms_date
            if last_sent and last_sent.date() == inactive_threshold:
                yield c

    for c in _contacts_to_remind():
        if c.default_connection:
            c.message(const.INACTIVE_CONTACT, **{})


def send_expected_deliveries(router_obj=None):
    """
    Weekly reminder for expected deliveries

    To: In Charge Contacts
    On: Weekly
    """
    _set_router(router_obj)

    incharge = ContactType.objects.get(slug='incharge')
    now = datetime.utcnow().date()
    next_week = now + timedelta(days=7)

    contacts = Contact.objects.filter(is_active=True, types=incharge,
                                      location__pregnantmother__edd__gte=now,
                                      location__pregnantmother__edd__lte=next_week) \
                        .annotate(num_edds=Count('location__pregnantmother'))

    for c in contacts:
        if c.default_connection:
            c.message(const.EXPECTED_EDDS, **{"edd_count": c.num_edds, })


def _create_notification(type, contact, mother_id):
    notif = ReminderNotification(type=type,
                                 recipient=contact,
                                 date=datetime.utcnow())
    notif.set_mother(mother_id)
    notif.save()
    return notif
