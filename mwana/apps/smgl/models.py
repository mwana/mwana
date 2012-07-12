from rapidsms.models import Contact, Connection
from django.db import models

# Create your models here.
from mwana.apps.locations.models import Location
from smscouchforms.models import FormReferenceBase
from mwana.apps.smgl import const

REASON_FOR_VISIT_CHOICES = (
    ('r', 'Routine'),
    ('nr', 'Non-Routine')
)

class XFormKeywordHandler(models.Model):
    keyword = models.CharField(max_length=255, help_text="The keyword that you want to associate with this handler.")
    function_path = models.CharField(max_length=255, help_text="The full path to the handler function. E.g: 'mwana.apps.smgl.app.birth_registration'")


class PregnantMother(models.Model):
    HI_RISK_REASONS = {
        "csec": "C-Section",
        "cmp": "Complications during previous pregnancy",
        "gd": "Gestational Diabetes",
        "hbp": "High Blood Pressure",
        "psb": "Previous still born",
        "oth": "Other",
        "none": "None"
    }
    
    contact = models.ForeignKey(Contact, help_text="The contact that registered this mother")
    location = models.ForeignKey(Location)
    first_name = models.CharField(max_length=160)
    last_name = models.CharField(max_length=160)
    uid = models.CharField(max_length=160, unique=True, help_text="The Unique Identifier associated with this mother")
    lmp = models.DateField(null=True, blank=True, help_text="Last Menstrual Period")
    edd = models.DateField(help_text="Estimated Date of Delivery", null=True, blank=True)
    next_visit = models.DateField(help_text="Date of next visit")
    reason_for_visit = models.CharField(max_length=160, choices=REASON_FOR_VISIT_CHOICES)
    zone = models.CharField(max_length=160, null=True, blank=True)
    
    risk_reason_csec = models.BooleanField(default=False)
    risk_reason_cmp = models.BooleanField(default=False)
    risk_reason_gd = models.BooleanField(default=False)
    risk_reason_hbp = models.BooleanField(default=False)
    risk_reason_psb = models.BooleanField(default=False)
    risk_reason_oth = models.BooleanField(default=False)
    risk_reason_none = models.BooleanField(default=False)

    @property
    def name(self):
        return "%s %s" % (self.first_name, self.last_name)
    
    def set_risk_reason(self, code, val=True):
        assert code in self.HI_RISK_REASONS
        setattr(self, "risk_reason_%s" % code, val)
    
    def get_risk_reason(self, code):
        assert code in self.HI_RISK_REASONS
        return getattr(self, "risk_reason_%s" % code)
    
    def get_risk_reasons(self):
        for c in self.HI_RISK_REASONS:
            if self.get_risk_reason(c):
                yield c
    
    def __unicode__(self):
        return 'Mother: %s %s, UID: %s' % (self.first_name, self.last_name, self.uid)

class MotherReferenceBase(models.Model):
    """
    An abstract base class to hold mothers. Provides some shared functionalityn
    and consistent field naming.
    """
    # Note: we capture both the mom UID and try to match it to a pregnant 
    # mother foreignkey. In the event that an ER is started for NOT a mother or
    # the UID is garbled/unmatcheable we still want to capture it for analysis.
    mother_uid = models.CharField(max_length=255, null=True, blank=True,
                                  help_text="Unique ID of mother")
    mother = models.ForeignKey(PregnantMother, null=True, blank=True)
    
    def set_mother(self, mother_id):
        self.mother_uid = mother_id
        try:
            self.mother = PregnantMother.objects.get(uid__iexact=mother_id)
        except PregnantMother.DoesNotExist:
            pass
    
    class Meta:
        abstract = True

class FacilityVisit(models.Model):
    """
    This is a store used to indicate the visit activity of the mother
    (Which facility she went to, when she did so, etc)
    """
    mother = models.ForeignKey(PregnantMother, related_name="facility_visits")
    location = models.ForeignKey(Location, help_text="The location of this visit")
    visit_date = models.DateField()
    reason_for_visit = models.CharField(max_length=255, help_text="The reason the mother visited the clinic",
                                        choices=REASON_FOR_VISIT_CHOICES)
    edd = models.DateField(null=True, blank=True, help_text="Updated Mother's Estimated Date of Deliver")
    next_visit = models.DateField()
    contact = models.ForeignKey(Contact, help_text="The contact that sent the information for this mother")

class AmbulanceRequest(models.Model):
    """
    Bucket for ambulance request info
    """
    contact = models.ForeignKey(Contact, help_text="Contact who initiated the emergency response",
                                null=True, blank=True, related_name="er_iniator")
    connection = models.ForeignKey(Connection, help_text="If not a registered contact, the connection " \
                                                         "of the person who initiated ER",
                                    null=True, blank=True)
    #Note: we capture both the mom UID and try to match it to a pregnant mother foreignkey. In the event that an ER
    #is started for NOT a mother or the UID is garbled/unmatcheable we still want to capture it for analysis.
    mother_uid = models.CharField(max_length=255, help_text="Unique ID of mother", null=True, blank=True)
    mother = models.ForeignKey(PregnantMother, null=True, blank=True)
    #Similarly it shouldn't matter if this field is filled in or not.
    danger_sign = models.CharField(max_length=255, null=True, blank=True,help_text="Danger signs that prompted the ER")
    from_location = models.ForeignKey(Location, null=True, blank=True,help_text="The Location the Emergency Request ORIGINATED from", related_name="from_location")

    ambulance_driver = models.ForeignKey(Contact, null=True, blank=True, help_text="The Ambulance Driver/Dispatcher who was contacted",related_name="ambulance_driver")

    triage_nurse = models.ForeignKey(Contact, null=True, blank=True, help_text="The Triage Nurse who was contacted",related_name="triage_nurse")

    other_recipient = models.ForeignKey(Contact, null=True, blank=True, help_text="Other Recipient of this ER",related_name="other_recipient")

    receiving_facility_recipient = models.ForeignKey(Contact, null=True, blank=True, help_text="Receiving Clinic Recipient of this ER",related_name="receiving_facility_recipient")
    receiving_facility = models.ForeignKey(Location, null=True, blank=True, help_text="The receiving facility",related_name="receiving_facility")

    requested_on = models.DateTimeField(auto_now_add=True)
    received_response = models.BooleanField(default=False)

class AmbulanceResponse(models.Model):
    ER_RESPONSE_CHOICES = (
        ('cancelled', 'Cancelled'),
        ('confirmed', 'Confirmed'),
        ('pending', 'Pending'),
    )

    #Note: we capture both the mom UID and try to match it to a pregnant mother foreignkey. In the event that an ER
    #is started for NOT a mother or the UID is garbled/unmatcheable we still want to capture it for analysis.
    responded_on = models.DateTimeField(auto_now_add=True, help_text="Date the response happened")
    mother_uid = models.CharField(max_length=255, help_text="Unique ID of mother", null=True, blank=True)
    mother = models.ForeignKey(PregnantMother, null=True, blank=True)
    ambulance_request = models.ForeignKey(AmbulanceRequest, null=True, blank=True)
    response = models.CharField(max_length=60, choices=ER_RESPONSE_CHOICES)
    responder = models. ForeignKey(Contact, help_text="The contact that responded to this ER event")


class AmbulanceOutcome(models.Model):
    ER_OUTCOME_CHOICES = (
        ('under-care', 'Under Care'),
        ('treated_discharged', 'Treated and Discharged'),
        ('deceased', 'Deceased'),
    )
    # Note: we capture both the mom UID and try to match it to a pregnant 
    # mother foreignkey. In the event that an ER is started for NOT a mother 
    # or the UID is garbled/unmatcheable we still want to capture it for analysis.
    outcome_on = models.DateTimeField(auto_now_add=True, help_text = "Date and Time this outcome was provided")
    mother_uid = models.CharField(max_length=255, help_text="Unique ID of mother", null=True, blank=True)
    mother = models.ForeignKey(PregnantMother, null=True, blank=True)
    ambulance_request = models.ForeignKey(AmbulanceRequest, null=True, blank=True)
    outcome = models.CharField(max_length=60, choices=ER_OUTCOME_CHOICES)


REFERRAL_STATUS_CHOICES = (("em", "emergent"), ("nem", "non-emergent"))
REFERRAL_OUTCOME_CHOICES = (("stb", "stable"), ("cri", "critical"),
                            ("dec", "deceased"))
DELIVERY_MODE_CHOICES = (("vag", "vaginal"), ("csec", "c-section"))

class Referral(FormReferenceBase, MotherReferenceBase):
    REFERRAL_REASONS = {
        "fd":    "Fetal Distress",
        "pec":   "Pre-Eclampsia",
        "ec":    "Eclampsia",
        "hbp":   "High Blood Pressure",
        "pph":   "Post-Partum Hemorrhage",
        "aph":   "Antepartum Hemorrhage",
        "pl":    "Prolonged Labor",
        "cpd":   "Big Baby Small Pelvis",
        "oth":   "Other",
    }
    date = models.DateTimeField()
    facility = models.ForeignKey(Location, 
                                 help_text="The referred facility")
    
    responded = models.BooleanField(default=False)
    mother_showed = models.NullBooleanField(default=None)
    
    status = models.CharField(max_length=3, 
                              choices=REFERRAL_STATUS_CHOICES,
                              null=True, blank=True)
    
    time = models.TimeField(help_text="Time of referral", null=True)
    
    # outcomes
    mother_outcome = models.CharField(max_length=3, 
                                      choices=REFERRAL_OUTCOME_CHOICES,
                                      null=True, blank=True)
    baby_outcome = models.CharField(max_length=3, 
                                    choices=REFERRAL_OUTCOME_CHOICES,
                                    null=True, blank=True)
    mode_of_delivery = models.CharField(max_length=4, 
                                        choices=DELIVERY_MODE_CHOICES,
                                        null=True, blank=True)
    
    # this will make reporting easier than dealing with another table
    reason_fd = models.BooleanField(default=False)
    reason_pec = models.BooleanField(default=False)
    reason_ec = models.BooleanField(default=False)
    reason_hbp = models.BooleanField(default=False)
    reason_pph = models.BooleanField(default=False)
    reason_aph = models.BooleanField(default=False)
    reason_pl = models.BooleanField(default=False)
    reason_cpd = models.BooleanField(default=False)
    reason_oth = models.BooleanField(default=False)
    
    
    def set_reason(self, code, val=True):
        assert code in self.REFERRAL_REASONS
        setattr(self, "reason_%s" % code, val)
    
    def get_reason(self, code):
        assert code in self.REFERRAL_REASONS
        return getattr(self, "reason_%s" % code)
    
    def get_reasons(self):
        for c in sorted(self.REFERRAL_REASONS.keys()):
            if self.get_reason(c):
                yield c
        
class PreRegistration(models.Model):
    LANGUAGES_CHOICES = (
        ('en', 'English'),
        ('to', 'Tonga'),
    )

    PRE_REG_TITLE_CHOICES = (
        (const.CTYPE_LAYCOUNSELOR, 'Community Based Agent'),
        (const.CTYPE_TRIAGENURSE, 'Triage Nurse'),
        (const.CTYPE_DATACLERK, 'Data Clerk'),
        ('worker', 'Clinic Worker'),
        ('DHO', 'District Health Officer'),
        ('DMHO', 'District mHealth Officer'),
        ('district', 'District Worker'),
        ('AM', 'Ambulance'),
    )
    contact = models.ForeignKey(Contact, null=True, blank=True)
    phone_number = models.CharField(max_length=255, help_text="User phone number", unique=True)
    unique_id = models.CharField(max_length=255, unique=True,
                                 help_text="The user's Unique ID")
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    location = models.ForeignKey(Location)
    title = models.CharField(max_length=255, help_text="User title", choices=PRE_REG_TITLE_CHOICES)
    zone = models.CharField(max_length=20, help_text="User Zone (optional)", blank=True, null=True)
    language = models.CharField(max_length=255, help_text="Preferred Language", default="english", choices=LANGUAGES_CHOICES)
    has_confirmed = models.BooleanField(default=False, help_text="Has this User confirmed their registration?")

GENDER_CHOICES = (("bo", "boy"), ("gi", "girl"))
PLACE_CHOICES = (("h", "home"), ("f", "facility"))

class BirthRegistration(models.Model):
    """
    Database representation of a birth registration form
    """
    contact = models.ForeignKey(Contact, null=True)
    connection = models.ForeignKey(Connection)
    mother = models.ForeignKey(PregnantMother, null=True, blank=True)
    date = models.DateField()
    gender = models.CharField(max_length=2, choices=GENDER_CHOICES)
    place = models.CharField(max_length=1, choices=PLACE_CHOICES)
    complications = models.BooleanField(default=False)
    number = models.IntegerField(default=1)

PERSON_CHOICES = (("ma", "mother"), ("inf", "infant"))

class DeathRegistration(models.Model):
    """
    Database representation of a death registration form
    """
    contact = models.ForeignKey(Contact, null=True)
    connection = models.ForeignKey(Connection)
    unique_id = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateField()
    person = models.CharField(max_length=3, choices=PERSON_CHOICES)
    place = models.CharField(max_length=1, choices=PLACE_CHOICES)
        
    
    