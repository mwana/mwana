from datetime import datetime, timedelta
from mwana.apps.smgl.models import FacilityVisit, ReminderNotification, Referral,\
    PregnantMother
from mwana.apps.smgl import const
from django.db.models import Q
from threadless_router.router import Router
from rapidsms import router

# reminders will be sent up to this amount late (if, for example the system
# was down.
SEND_REMINDER_LOWER_BOUND = timedelta(days=2)

def _set_router():
    # this hack sets the global router to threadless router.
    # should maybe be cleaned up.
    router.router = Router()
    
def send_followup_reminders():
    """
    Next visit date from Pregnancy registration or Follow-up visit should
    be used to generate reminder for the next appointment.
    
    To: CBA
    On: 7 days before visit date
    """
    _set_router()
    now = datetime.utcnow().date()
    reminder_threshold = now + timedelta(days=7) 
    visits_to_remind = FacilityVisit.objects.filter(
        next_visit__gte=reminder_threshold - SEND_REMINDER_LOWER_BOUND,
        next_visit__lte=reminder_threshold,
        reminded=False)
    for v in visits_to_remind:
        found_someone = False
        for c in v.mother.get_laycounselors():
            found_someone = True
            c.message(const.REMINDER_FU_DUE,
                      **{"name": v.mother.name,
                         "unique_id": v.mother.uid,
                         "loc": v.location.name})
            _create_notification("nvd", c, v.mother.uid)
        if found_someone:
            v.reminded = True
            v.save()
    

def send_non_emergency_referral_reminders():
    """
    Reminder for non-emergency referral.
    
    To: CBA
    On: 7 days after referral is registered in the system
    
    Reminder is not necessary if mother shows up in the referral center. 
    Also If we don't have the mother details (safe motherhood ID, Zone...) 
    then the server does nothing.
    """
    _set_router()
    now = datetime.utcnow()
    reminder_threshold = now - timedelta(days=7)
    referrals_to_remind = Referral.non_emergencies().filter(
        reminded=False,
        date__gte=reminder_threshold - SEND_REMINDER_LOWER_BOUND,
        date__lte = reminder_threshold
    ).filter(Q(mother_showed=None) | Q(mother_showed=False))
    referrals_to_remind = referrals_to_remind.exclude(mother=None)
        
    for ref in referrals_to_remind:
        found_someone = False
        for c in ref.mother.get_laycounselors():
            found_someone = True
            c.message(const.REMINDER_NON_EMERGENCY_REFERRAL,
                      **{"name": ref.mother.name,
                         "unique_id": ref.mother.uid,
                         "loc": ref.facility.name})
            _create_notification("nem_ref", c, ref.mother.uid)
        if found_someone:
            ref.reminded = True
            ref.save()
    
def send_emergency_referral_reminders():
    """
    Reminder to collect outcomes for emergency referrals.
    
    To: Data Clerk operating at the referral facility
    On: 3 days after referral had been entered
    """
    _set_router()
    now = datetime.utcnow()
    reminder_threshold = now - timedelta(days=3)
    referrals_to_remind = Referral.emergencies().filter(
        reminded=False,
        responded=False,
        date__gte=reminder_threshold - SEND_REMINDER_LOWER_BOUND,
        date__lte = reminder_threshold
    ).exclude(mother_uid=None)
    for ref in referrals_to_remind:
        found_someone = False
        for c in ref.get_receiving_data_clerks():
            found_someone = True
            c.message(const.REMINDER_EMERGENCY_REFERRAL,
                      **{"unique_id": ref.mother_uid,
                         "date": ref.date.date(),
                         "loc": ref.referring_facility.name if ref.referring_facility else "?"})
            _create_notification("em_ref", c, ref.mother_uid)
        if found_someone:
            ref.reminded = True
            ref.save()


def send_upcoming_delivery_reminders():
    """
    Reminders for upcoming delivery     
    
    To: CBA
    On: 14 days prior expected delivery day    
    
    Cancel reminders after notification of birth. 
    """
    _set_router()
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
            found_someone = True
            c.message(const.REMINDER_UPCOMING_DELIVERY,
                      **{"name": mom.name,
                         "unique_id": mom.uid,
                         "date": mom.edd})
            _create_notification("edd_14", c, mom.uid)
        if found_someone:
            mom.reminded = True
            mom.save()

    
def _create_notification(type, contact, mother_id):
    notif = ReminderNotification(type=type, 
                                 recipient=contact,
                                 date=datetime.utcnow())
    notif.set_mother(mother_id)
    notif.save()
    return notif
    