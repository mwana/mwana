from rapidsms.models import Contact
from django.db import models

# Create your models here.
from mwana.apps.locations.models import Location

REASON_FOR_VISIT_CHOICES = (
    ('initial_registration', 'Initial Registration'),
    ('scheduled_checkup', 'Normal Scheduled Visit'),
    ('referral', 'Referral from other Facility'),
    ('emergency', 'Emergency visit from other Facility'),
    ('routine', 'Routine Visit'),
    ('non-routine', 'Non-Routine Visit'),
    ('other', 'Other'),
)

class XFormKeywordHandler(models.Model):
    keyword = models.CharField(max_length=255, help_text="The keyword that you want to associate with this handler.")
    function_path = models.CharField(max_length=255, help_text="The full path to the handler function. E.g: 'mwana.apps.smgl.app.birth_registration'")

class PregnantMother(models.Model):
    contact = models.ForeignKey(Contact, help_text="The contact that registered this mother")
    location = models.ForeignKey(Location)
    first_name = models.CharField(max_length=160)
    last_name = models.CharField(max_length=160)
    uid = models.CharField(max_length=160, unique=True, help_text="The Unique Identifier associated with this mother")
    lmp = models.DateField(null=True, blank=True, help_text="Last Menstrual Period")
    edd = models.DateField(help_text="Estimated Date of Delivery", null=True, blank=True)
    high_risk_history = models.CharField(max_length=160, help_text="The code indicating any high risk issues for this pregnant mother")
    next_visit = models.DateField(help_text="Date of next visit")
    reason_for_visit = models.CharField(max_length=160, choices=REASON_FOR_VISIT_CHOICES)
    zone = models.CharField(max_length=160, null=True, blank=True)

    def __unicode__(self):
        return 'Mother: %s %s, UID: %s' % (self.first_name, self.last_name, self.uid)

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
    next_visit = models.DateField()
    contact = models.ForeignKey(Contact, help_text="The contact that sent the information for this mother")


class PreRegistration(models.Model):
    LANGUAGES_CHOICES = (
        ('en', 'English'),
        ('ton', 'Tonga'),
    )

    PRE_REG_TITLE_CHOICES = (
        ('CBA', 'Community Based Agent'),
        ('TN', 'Triage Nurse'),
        ('DA', 'Data Associate'),
        ('worker', 'Clinic Worker'),
        ('DMO', 'DMO'),
        ('AM', 'Ambulance'),
        ('ER', 'Emergency Responder'),
    )
    contact = models.ForeignKey(Contact, null=True, blank=True)
    phone_number = models.CharField(max_length=255, help_text="User phone number", unique=True)
    unique_id = models.CharField(max_length=255, help_text="The user's Unique ID")
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    facility_name = models.CharField(max_length=255, null=True, blank=True)
    facility_code = models.CharField(max_length=255, help_text="The code for this facility (REQUIRED)")
    title = models.CharField(max_length=255, help_text="User title", choices=PRE_REG_TITLE_CHOICES)
    zone = models.CharField(max_length=20, help_text="User Zone (optional)", blank=True, null=True)
    language = models.CharField(max_length=255, help_text="Preferred Language", default="english", choices=LANGUAGES_CHOICES)
