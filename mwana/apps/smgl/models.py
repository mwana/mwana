from rapidsms.models import Contact, Connection
from django.db import models

# Create your models here.
from mwana.apps.locations.models import Location
from smscouchforms.models import FormReferenceBase
from mwana.apps.smgl import const
from mwana.apps.contactsplus.models import ContactType

REASON_FOR_VISIT_CHOICES = (
    ('r', 'Routine'),
    ('nr', 'Non-Routine')
)

VISIT_TYPE_CHOICES = (
    ('anc', 'ANC'),
    ('pos', 'POS')
)

POS_STATUS_CHOICES = (
    ('good', 'Good'),
    ('fair', 'Fair'),
    ('ill', 'Ill'),
    ('critical', 'Critical')
)


class XFormKeywordHandler(models.Model):
    """
    System configuration that links xform keywords to functions for post
    processing.
    """
    keyword = models.CharField(max_length=255, help_text="The keyword that you want to associate with this handler.")
    function_path = models.CharField(max_length=255, help_text="The full path to the handler function. E.g: 'mwana.apps.smgl.app.birth_registration'")

    def __unicode__(self):
        return self.keyword.upper()

    class Meta:
        ordering = ['keyword', ]


class PregnantMother(models.Model):
    """
    Representation of a pregnant mother in SMGL.
    """

    HI_RISK_REASONS = {
        "csec": "C-Section",
        "cmp": "Complications during previous pregnancy",
        "gd": "Gestational Diabetes",
        "hbp": "High Blood Pressure",
        "psb": "Previous still born",
        "oth": "Other",
        "none": "None"
    }

    created_date = models.DateTimeField(null=True, blank=True)
    contact = models.ForeignKey(Contact, help_text="The contact that registered this mother")
    location = models.ForeignKey(Location)
    first_name = models.CharField(max_length=160)
    last_name = models.CharField(max_length=160)
    uid = models.CharField(max_length=160, unique=True,
                           help_text="The Unique Identifier associated with this mother")
    lmp = models.DateField(null=True, blank=True, help_text="Last Menstrual Period")
    edd = models.DateField(help_text="Estimated Date of Delivery", null=True, blank=True)
    next_visit = models.DateField(help_text="Date of next visit")
    reason_for_visit = models.CharField(max_length=160, choices=REASON_FOR_VISIT_CHOICES)
    zone = models.ForeignKey(Location, null=True, blank=True,
                             related_name="pregnant_mother_zones")

    risk_reason_csec = models.BooleanField(default=False)
    risk_reason_cmp = models.BooleanField(default=False)
    risk_reason_gd = models.BooleanField(default=False)
    risk_reason_hbp = models.BooleanField(default=False)
    risk_reason_psb = models.BooleanField(default=False)
    risk_reason_oth = models.BooleanField(default=False)
    risk_reason_none = models.BooleanField(default=False)

    reminded = models.BooleanField(default=False)

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

    def get_laycounselors(self):
        """
        Given a mother, get the lay counselors who should be notified about
        her registration / reminded for followups
        """
        # TODO: determine exactly how this should work.
        return Contact.objects.filter(
                types=ContactType.objects.get(
                            slug__iexact=const.CTYPE_LAYCOUNSELOR
                            ),
                location=self.zone,
                is_active=True)

    def __unicode__(self):
        return 'Mother: %s %s, UID: %s' % (self.first_name, self.last_name, self.uid)


class MotherReferenceBase(models.Model):
    """
    An abstract base class to hold mothers. Provides some shared functionality
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
    created_date = models.DateTimeField(null=True, blank=True)

    mother = models.ForeignKey(PregnantMother, related_name="facility_visits")
    location = models.ForeignKey(Location, help_text="The location of this visit")
    district = models.ForeignKey(Location, help_text="The district for this location",
                                 null=True, blank=True,
                                 related_name="district_location")

    visit_date = models.DateField()
    visit_type = models.CharField(max_length=255, help_text="ANC or POS visit",
                                  choices=VISIT_TYPE_CHOICES,
                                  default='anc')
    reason_for_visit = models.CharField(max_length=255, help_text="The reason the mother visited the clinic",
                                        choices=REASON_FOR_VISIT_CHOICES)
    edd = models.DateField(null=True, blank=True, help_text="Updated Mother's Estimated Date of Deliver")
    next_visit = models.DateField(null=True, blank=True)
    contact = models.ForeignKey(Contact, help_text="The contact that sent the information for this mother")
    reminded = models.BooleanField(default=False)
    mother_status = models.CharField(max_length=8, help_text="Mother's Status",
                                     choices=POS_STATUS_CHOICES,
                                     null=True, blank=True)
    baby_status = models.CharField(max_length=8, help_text="Baby's Status",
                                     choices=POS_STATUS_CHOICES,
                                     null=True, blank=True)
    referred = models.BooleanField(default=False)

    def is_latest_for_mother(self):
        return FacilityVisit.objects.filter(mother=self.mother)\
            .order_by("-created_date")[0] == self

    def save(self, *args, **kwargs):
        """
        Sets the district associated with the current location
        """
        location = self.location
        loc_type = location.type.singular.lower()
        while loc_type != 'district':
            location = location.parent
            loc_type = location.type.singular.lower()
        self.district = location
        super(FacilityVisit, self).save(*args, **kwargs)


class AmbulanceRequest(FormReferenceBase, MotherReferenceBase):
    """
    Bucket for ambulance request info
    """
    ambulance_driver = models.ForeignKey(Contact, null=True, blank=True, help_text="The Ambulance Driver/Dispatcher who was contacted", related_name="ambulance_driver")
    triage_nurse = models.ForeignKey(Contact, null=True, blank=True, help_text="The Triage Nurse who was contacted", related_name="triage_nurse")
    other_recipient = models.ForeignKey(Contact, null=True, blank=True, help_text="Other Recipient of this ER", related_name="other_recipient")


class AmbulanceResponse(FormReferenceBase, MotherReferenceBase):
    ER_RESPONSE_CHOICES = (
        ('na', 'Not Available'),
        ('dl', 'Delayed'),
        ('otw', 'On The Way'),
    )

    responded_on = models.DateTimeField(auto_now_add=True, help_text="Date the response happened")
    ambulance_request = models.ForeignKey(AmbulanceRequest, null=True, blank=True)
    response = models.CharField(max_length=60, choices=ER_RESPONSE_CHOICES)
    responder = models.ForeignKey(Contact, help_text="The contact that responded to this ER event")


REFERRAL_STATUS_CHOICES = (("em", "emergent"), ("nem", "non-emergent"))
REFERRAL_OUTCOME_CHOICES = (("stb", "stable"), ("cri", "critical"),
                            ("dec", "deceased"), ("oth", "other"))
DELIVERY_MODE_CHOICES = (("vag", "vaginal"), ("csec", "c-section"),
                         ("pp", "post-partum"), ("ref", "new_referral"),
                            ("oth", "other"))


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
        "pp":    "post-partum visit"
    }
    date = models.DateTimeField()
    facility = models.ForeignKey(Location,
                                 help_text="The referred facility")
    from_facility = models.ForeignKey(Location,
                                      null=True, blank=True,
                                      help_text="The referring facility",
                                      related_name="referrals_made")

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
    reason_pp = models.BooleanField(default=False)

    reminded = models.BooleanField(default=False)
    amb_req = models.ForeignKey(AmbulanceRequest, null=True, blank=True)

    def set_reason(self, code, val=True):
        assert code in self.REFERRAL_REASONS, "%s is not a valid referral reason" % code
        setattr(self, "reason_%s" % code, val)

    def get_reason(self, code):
        assert code in self.REFERRAL_REASONS
        return getattr(self, "reason_%s" % code)

    def get_reasons(self):
        for c in sorted(self.REFERRAL_REASONS.keys()):
            if self.get_reason(c):
                yield c

    @classmethod
    def non_emergencies(cls):
        return cls.objects.filter(status="nem")

    @classmethod
    def emergencies(cls):
        return cls.objects.filter(status="em")

    @property
    def is_emergency(self):
        return self.status == "em"

    @property
    def referring_facility(self):
        if self.from_facility:
            return self.from_facility
        try:
            # hack: pre 9/28 this property was not set, so
            # set it on access and return it
            loc = self.session.connection.contact.location
            self.from_facility = loc
            self.save()
            return loc
        except AttributeError:
            # looks like the contact disappeared or no longer
            # has a location set. not much to be done.
            return None

    def get_receiving_data_clerks(self):
        # people who need to be reminded to collect the outcome
        return Contact.objects.filter(types__slug=const.CTYPE_DATACLERK,
                                      location=self.facility,
                                      is_active=True)

    @property
    def ambulance_response(self):
        response = 'non-em'
        if self.status == 'em':
            if self.amb_req:
                try:
                    response = self.amb_req.ambulanceresponse_set.all()[0].response
                except:
                    response = None
            else:
                response = "No Data"
        return response

    @property
    def outcome(self):
        outcome = self.mother_outcome if self.mother_outcome else ''
        if self.baby_outcome:
            outcome = '{}/{}'.format(outcome, self.baby_outcome)
        return outcome

    @property
    def flag(self):
        if self.status == 'em':
            if self.ambulance_response and not self.outcome:
                return 'resp-no-out'
            elif self.ambulance_response and self.outcome:
                return 'resp-out'
            else:
                return 'no-resp-no-out'
        return ''


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


class BirthRegistration(FormReferenceBase):
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
    district = models.ForeignKey(Location, null=True,
                                 related_name='birth_district')
    facility = models.ForeignKey(Location, null=True,
                                 related_name='birth_facility')
    location = models.ForeignKey(Location, null=True,
                                 related_name='birth_location')


PERSON_CHOICES = (("ma", "mother"), ("inf", "infant"))


class DeathRegistration(FormReferenceBase):
    """
    Database representation of a death registration form
    """
    contact = models.ForeignKey(Contact, null=True)
    connection = models.ForeignKey(Connection)
    unique_id = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateField()
    person = models.CharField(max_length=3, choices=PERSON_CHOICES)
    place = models.CharField(max_length=1, choices=PLACE_CHOICES)
    district = models.ForeignKey(Location, null=True,
                                 related_name='death_district')
    facility = models.ForeignKey(Location, null=True,
                                 related_name='death_facility')
    location = models.ForeignKey(Location, null=True,
                                 related_name='death_location')


REMINDER_TYPE_CHOICES = (("nvd", "Next Visit Date"),
                         ("pos", "POS Next Visit Date"),
                         ("em_ref", "Emergency Referral"),
                         ("nem_ref", "Non-Emergency Referral"),
                         ("edd_14", "Expected Delivery, 14 days before"),
                         ("syp", "Syphilis Treatment"))


class ReminderNotification(MotherReferenceBase):
    """
    Any notifications sent to user
    """
    type = models.CharField(max_length=10, choices=REMINDER_TYPE_CHOICES)
    recipient = models.ForeignKey(Contact,
                                  related_name='sent_notifications')
    date = models.DateTimeField()

    def __unicode__(self):
        return '%s sent to %s on %s' % (self.type,
                                        self.recipient,
                                        self.date)

TOLD_TYPE_CHOICES = (("edd", 'Expected Delivery Date'),
                     ("nvd", "Next Visit Date"),
                     ("ref", "Referral"))


class ToldReminder(FormReferenceBase, MotherReferenceBase):
    """
    Database representation of a told reminder form. Tracks records
    of users telling/reminder Mothers of important data.
    """
    contact = models.ForeignKey(Contact, null=True)
    date = models.DateTimeField()
    type = models.CharField(max_length=3, choices=TOLD_TYPE_CHOICES)


SYPHILIS_TEST_RESULT_CHOICES = (
                     ("p", 'Positive'),
                     ("n", "Negative")
                     )

SYPHILIS_SHOT_NUMBER_CHOICES = (
                     ("s1", 'S1'),
                     ("s2", "S2"),
                     ("s3", 'S3')
                     )


class SyphilisTest(FormReferenceBase, MotherReferenceBase):
    """
    Database representation of a syphilis test form. Tracks test results.
    """
    date = models.DateField()
    result = models.CharField(max_length=1,
                              choices=SYPHILIS_TEST_RESULT_CHOICES)
    district = models.ForeignKey(Location, help_text="The district for this location",
                                 null=True, blank=True)


class SyphilisTreatment(FormReferenceBase, MotherReferenceBase):
    """
    Database representation of a syphilis treatment form. Tracks treatment
    """
    date = models.DateField()
    shot_number = models.CharField(max_length=2,
                              choices=SYPHILIS_SHOT_NUMBER_CHOICES)
    next_visit_date = models.DateField(null=True, blank=True)
    reminded = models.BooleanField(default=False)
    district = models.ForeignKey(Location, help_text="The district for this location",
                                 null=True, blank=True)

    def is_latest_for_mother(self):
        return SyphilisTreatment.objects.filter(mother=self.mother)\
            .order_by("-date")[0] == self

