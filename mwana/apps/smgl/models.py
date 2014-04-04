from rapidsms.models import Contact, Connection
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned

# Create your models here.
from mwana.apps.locations.models import Location
from smscouchforms.models import FormReferenceBase
from rapidsms.contrib.messagelog.models import Message
from mwana.apps.smgl import const
from mwana.apps.contactsplus.models import ContactType
import datetime
import ntpath

REASON_FOR_VISIT_CHOICES = (
    ('r', 'Routine'),
    ('nr', 'Non-Routine')
)

VISIT_TYPE_CHOICES = (
    ('anc', 'ANC'),
    ('pos', 'POS')
)

POS_STATUS_CHOICES = (
    ('well', 'Well'),
    ('sick', 'Sick')
)


class XFormKeywordHandler(models.Model):

    """
    System configuration that links xform keywords to functions for post
    processing.
    """
    keyword = models.CharField(
        max_length=255,
        help_text="The keyword that you want to associate with this handler.")
    function_path = models.CharField(
        max_length=255,
        help_text="The full path to the handler function. E.g: \
        'mwana.apps.smgl.app.birth_registration'")

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
    contact = models.ForeignKey(
        Contact, help_text="The contact that registered this mother")
    location = models.ForeignKey(Location)
    first_name = models.CharField(max_length=160)
    last_name = models.CharField(max_length=160)
    uid = models.CharField(max_length=160, unique=True,
                           help_text="The Unique Identifier associated with \
                           this mother")
    lmp = models.DateField(
        null=True, blank=True, help_text="Last Menstrual Period")
    edd = models.DateField(
        help_text="Estimated Date of Delivery", null=True, blank=True)
    next_visit = models.DateField(help_text="Date of next visit")
    reason_for_visit = models.CharField(
        max_length=160, choices=REASON_FOR_VISIT_CHOICES)
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


    def get_field_value_mapping(self):
        mapped_text = "MotherID={self.uid}, Name={self.first_name} \
        {self.last_name}, LMP={lmp}, EDD={edd}, NVD={nvd}, \
        Visit Reason={visit_reasons}, Risk Reason={risk_reasons}, \
        Location={self.location},  Zone={self.zone.name}".format(
            self=self,
            visit_reasons=self.get_reason_for_visit_display(),
            risk_reasons=", ".join(self.get_risk_reasons()),
            lmp=self.lmp.strftime('%d %b %Y') if self.lmp else None,
            edd=self.edd.strftime('%d %b %Y') if self.edd else None,
            nvd=self.next_visit.strftime('%d %b %Y') if self.next_visit else
            None
        )
        return mapped_text

    @property
    def has_delivered(self):
        if not self.edd:
            return True
        if self.birthregistration_set.all():
            return True
        before_edd = self.edd - datetime.timedelta(days=1)
        after_edd = self.edd + datetime.timedelta(days=1)
        try:
            birth = self.birthregistration_set.filter(
                date__range=[before_edd, after_edd])[0]
        except IndexError:
            if datetime.datetime.now().date() > (self.edd + datetime.timedelta(days=30)):
                return True #If we are 30 days past the edd
            else:
                return False
        else:
            return True

    @property
    def birth_location(self):
        if not self.has_delivered:
            return "Not Delivered"
        elif not self.birthregistration_set.all():
            return "Unregistered"
        else:
            return self.birthregistration_set.all()[0].get_place_display()

    @property
    def birth(self):
        if not self.has_delivered:
            return False
        try:
            birth = self.birthregistration_set.all()[0]
        except IndexError:
            return False
        else:
            return birth


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

    def has_risk_reasons(self):
        risk_reasons = [reason for reason in self.get_risk_reasons()]
        if not risk_reasons or risk_reasons == ['none']:
            return False
        else:
            return True

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


    def get_gestational_age(self):
        if not self.lmp:
            return 0
        if not self.created_date:
            return 0
        gestational_age = self.created_date.date() - self.lmp
        return gestational_age.days

    def __unicode__(self):
        return 'Mother: %s %s, UID: %s' % (
            self.first_name,
            self.last_name,
            self.uid
        )

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
    location = models.ForeignKey(
        Location, help_text="The location of this visit")
    district = models.ForeignKey(
        Location, help_text="The district for this location",
        null=True, blank=True,
        related_name="district_location")
    visit_date = models.DateField()
    visit_type = models.CharField(max_length=255, help_text="ANC or POS visit",
                                  choices=VISIT_TYPE_CHOICES,
                                  default='anc')
    reason_for_visit = models.CharField(
        max_length=255, help_text="The reason the mother visited the clinic",
        choices=REASON_FOR_VISIT_CHOICES)
    edd = models.DateField(
        null=True, blank=True,
        help_text="Updated Mother's Estimated Date of Deliver")
    next_visit = models.DateField(null=True, blank=True)
    contact = models.ForeignKey(
        Contact,
        help_text="The contact that sent the information for this mother")
    reminded = models.BooleanField(default=False)
    mother_status = models.CharField(max_length=4, help_text="Mother's Status",
                                     choices=POS_STATUS_CHOICES,
                                     null=True, blank=True)
    baby_status = models.CharField(max_length=4, help_text="Baby's Status",
                                   choices=POS_STATUS_CHOICES,
                                   null=True, blank=True)
    referred = models.BooleanField(default=False)

    def previous_visit(self):
        all_visits = FacilityVisit.objects.filter(
            mother=self.mother
            ).order_by('created_date')
        visit_index = 0
        for index, visit in enumerate(all_visits):
            if self == visit:
                visit_num = index
                break
        if visit_index > 0:
            return all_visits[visit_index-1]
        else:
            return False

    def told(self):
        #Tolds sent since last visit
        previous_visit =  self.previous_visit()
        if previous_visit:
            tolds = ToldReminder.objects.filter(
                date__gte=previous_visit.visit_date,
                date__lte=self.visit_date,
                mother=self.mother
                ).filter(type='nvd')
        else:
            tolds = ToldReminder.objects.filter(
                date__lte=self.visit_date,
                mother=self.mother).filter(type='nvd')
        try:
            told = tolds[0]
        except IndexError:
            return False
        else:
            return told

    def is_on_time(self):
        told = self.told()
        if told:
            before = told.date - datetime.timedelta(days=14)
            after = told.date + datetime.timedelta(days=14)
            if self.visit_date >= before.date() and self.visit_date <= after.date():
                return True
            else:
                return False

    def get_field_value_mapping(self):
        # The edd only makes sense for ANC visits and if not set on the
        # facility visit object, we will look at the mother edd.
        if self.visit_type.lower() == "anc":
            edd = self.edd or self.mother.edd
            data = {'self': self,
                    'visit_type': self.get_visit_type_display(),
                    'visit_reason': self.get_reason_for_visit_display(),
                    'nvd': self.next_visit.strftime('%d %b %Y')
                    if self.next_visit else None,
                    'visit_date': self.visit_date.strftime('%d %b %Y'),
                    'edd': edd.strftime('%d %b %Y') if edd else ' '}
            mapped_text = "MotherID={self.mother.uid}, Location={self.location}\
            ,  Visit Type={visit_type}, Reason for Visit={visit_reason},\
            Visit Date={visit_date}, Next Visit Date={nvd}, EDD={edd}".format(
                **data
            )
        else:
            data = {'self': self,
                    'visit_type': self.get_visit_type_display(),
                    'mother_status': self.get_mother_status_display(),
                    'baby_status': self.get_baby_status_display(),
                    'visit_date': self.visit_date.strftime('%d %b %Y')
                    if self.visit_date else None,
                    'nvd': self.next_visit.strftime('%d %b %Y')
                    if self.next_visit else None,
                    }
            mapped_text = "MotherID={self.mother.uid}, Location={self.location}, Visit Date={visit_date}, Visit Type={visit_type},\
            Mother Status={mother_status}, Baby Status={baby_status}, Next Visit Date={nvd}, Referred={self.referred}".format(**data)
        return mapped_text

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
    ambulance_driver = models.ForeignKey(
        Contact, null=True, blank=True,
        help_text="The Ambulance Driver/Dispatcher who was contacted",
        related_name="ambulance_driver")
    triage_nurse = models.ForeignKey(
        Contact, null=True, blank=True,
        help_text="The Triage Nurse who was contacted",
        related_name="triage_nurse")
    other_recipient = models.ForeignKey(
        Contact, null=True, blank=True,
        help_text="Other Recipient of this ER",
        related_name="other_recipient")


class AmbulanceResponse(FormReferenceBase, MotherReferenceBase):
    ER_RESPONSE_CHOICES = (
        ('na', 'Not Available'),
        ('dl', 'Delayed'),
        ('otw', 'On The Way'),
    )

    responded_on = models.DateTimeField(
        auto_now_add=True, help_text="Date the response happened"
        )
    ambulance_request = models.ForeignKey(
        AmbulanceRequest, null=True, blank=True)
    response = models.CharField(max_length=60, choices=ER_RESPONSE_CHOICES)
    responder = models.ForeignKey(
        Contact, help_text="The contact that responded to this ER event")


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
        assert code in self.REFERRAL_REASONS, "%s is not a valid \
        referral reason" % code
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
                    response = self.amb_req.ambulanceresponse_set.all()[
                        0].response
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

    def amb_responders(self):
        try:
            amb_responders = ", ".join(
                amb_resp.responder.name for amb_resp in self.amb_req.ambulanceresponse_set.all())
        except AttributeError:
            return ""
        else:
            return amb_responders

    @property
    def date_outcome(self):
        if self.mother_outcome:
            refout_message = "refout %s" % self.mother_uid
            try:
                message = Message.objects.filter(
                    text__istartswith=refout_message)[0]
            except IndexError:
                return ""
            else:
                return message.date
        else:
            return ""

    def turn_around_time(self):
        if not self.date_outcome:
            return 0
        else:
            turn_around = self.date_outcome - self.date
            return turn_around.seconds



class PreRegistration(models.Model):
    LANGUAGES_CHOICES = (
        ('en', 'English'),
        ('to', 'Tonga'),
    )

    PRE_REG_TITLE_CHOICES = (
        (const.CTYPE_LAYCOUNSELOR, 'Community Based Agent'),
        (const.CTYPE_TRIAGENURSE, 'Triage Nurse'),
        (const.CTYPE_DATACLERK, 'Data Clerk'),
        (const.CTYPE_INCHARGE, 'In Charge'),
        ('worker', 'Clinic Worker'),
        ('DHO', 'District Health Officer'),
        ('DMHO', 'District mHealth Officer'),
        ('district', 'District Worker'),
        ('AM', 'Ambulance'),
    )
    contact = models.ForeignKey(Contact, null=True, blank=True)
    phone_number = models.CharField(
        max_length=255, help_text="User phone number", unique=True)
    unique_id = models.CharField(max_length=255, unique=True,
                                 help_text="The user's Unique ID")
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    location = models.ForeignKey(Location)
    title = models.CharField(
        max_length=255, help_text="User title", choices=PRE_REG_TITLE_CHOICES)
    zone = models.CharField(
        max_length=20, help_text="User Zone (optional)", blank=True, null=True)
    language = models.CharField(
        max_length=255,
        help_text="Preferred Language",
        default="english",
        choices=LANGUAGES_CHOICES)
    has_confirmed = models.BooleanField(
        default=False, help_text="Has this User confirmed their registration?")

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


    def told(self):
        try:
            told = ToldReminder.objects.filter(
                type='edd_14',
                date__lte=self.date,
                mother=self.mother)
        except IndexError:
            return False
        else:
            return told

    def birth_on_time(self):
        told = self.told()
        if told:
            before = told.date - datetime.timedelta(days=21)
            after = told.date + datetime.timedelta(days=21)
            if self.date >= before and self.date <= after:
                return True
            else:
                return False
        else:
            return False

    def get_field_value_mapping(self):
        if self.mother:
            mother_id = self.mother.uid
        else:
            mother_id = None

        mapped_text = "MotherID={smh_id}, Gender={gender}, Date={date},\
         Place of Birth={place}, Complications={self.location}, \
         Number of Children={self.number}".format(
            self=self,
            smh_id=mother_id,
            date=self.date.strftime('%d %b %Y'),
            gender=self.get_gender_display(
            ).title(),
            place=self.get_place_display().title())
        return mapped_text

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

    def get_field_value_mapping(self):
        text = 'Date={date}, Person={person}, Place of Death={place}'.format(
            date=self.date.strftime('%d %b %Y'),
            person=self.get_person_display().title(),
            place=self.get_place_display().title(),
        )

        if self.unique_id:
            text = "MotherID={unique_id}, {text}".format(
                unique_id=self.unique_id, text=text)

        return text

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

    def get_field_value_mapping(self):
        return "MotherID={mother_id}, date={date_told}, Told Type={told_type}"\
            .format(mother_id=self.mother.uid,
                    date_told=self.date.strftime('%d %b %Y'),
                    told_type=self.get_type_display()
                    )

    def get_told_type(self):
        try:
            birth = BirthRegistration.objects.get(mother=self.mother)
        except BirthRegistration.DoesNotExist:
            return 'anc'
        except MultipleObjectsReturned:
            return 'pos'
        else:
            if birth.date > self.date.date():
                return 'pos'
            else:
                return 'anc'


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
    district = models.ForeignKey(
        Location, help_text="The district for this location",
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
    district = models.ForeignKey(
        Location, help_text="The district for this location",
        null=True, blank=True)

    def is_latest_for_mother(self):
        return SyphilisTreatment.objects.filter(mother=self.mother)\
            .order_by("-date")[0] == self


class Suggestion(models.Model):

    """
    Database representation of a story that also acts as a comment when
    attatched to an existing story"""
    title = models.CharField(max_length=255)
    authors = models.ManyToManyField(User)
    created_time = models.DateTimeField(auto_now_add=True)
    last_edited_time = models.DateTimeField(auto_now=True)
    parent_suggestion = models.ForeignKey('self', null=True, blank=True)
    text = models.TextField()
    closed = models.BooleanField(default=False)
    close_comment = models.TextField(null=True, blank=True)

    def get_authors_names(self):

        return ", ".join([user.username for user in self.authors.all()])

    def get_status(self):
        return 'Closed' if self.closed else 'Pending'

    class Meta:
        ordering = ('created_time', )

    def __unicode__(self):
        return self.title


class FileUpload(models.Model):
    suggestion = models.ForeignKey(Suggestion, related_name="attached_files")
    posted_by = models.ForeignKey(User)
    created_time = models.DateTimeField(auto_now_add=True)
    file = models.FileField(max_length=255, upload_to="attachments", null=True)

    def __unicode__(self):
        return self.original_name()

    def original_name(self):
        head, tail = ntpath.split(self.file.file.name)
        return tail or ntpath.basename(head)
