from rapidsms.models import Contact, Connection
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
    visit_date = models.DateField(auto_now_add=True)
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
    danger_sign = models.CharField(max_length=255, null=True, blank=True,
                            help_text="Danger signs that prompted the ER")
    from_location = models.ForeignKey(Location, null=True, blank=True,
                                help_text="The Location the Emergency Request ORIGINATED from",
                                related_name="from_location")

    ambulance_driver = models.ForeignKey(Contact, null=True, blank=True,
                                        help_text="The Ambulance Driver/Dispatcher who was contacted",
                                        related_name="ambulance_driver")
    ad_msg_sent = models.BooleanField(default=False, help_text="Was the initial ER notification sent to the Ambulance?")
    ad_confirmed = models.BooleanField(default=False, help_text="Has the Ambulance Driver confirmed receipt of this ER?")
    ad_confirmed_on = models.DateTimeField(null=True, blank=True, help_text="When did the Ambulance Driver confirm?")

    tn_msg_sent = models.BooleanField(default=False, help_text="Was the initial ER notification sent to the Triage Nurse?")
    triage_nurse = models.ForeignKey(Contact, null=True, blank=True, help_text="The Triage Nurse who was contacted",
                                    related_name="triage_nurse")
    tn_confirmed = models.BooleanField(default=False, help_text="Has the Triage Nurse confirmed receipt of this ER?")
    tn_confirmed_on = models.DateTimeField(null=True, blank=True, help_text="When did the Traige Nurse confirm?")

    other_msg_sent = models.BooleanField(default=False, help_text="Was the initial ER notification sent to the Other Recipient?")
    other_recipient = models.ForeignKey(Contact, null=True, blank=True, help_text="Other Recipient of this ER",
                                        related_name="other_recipient")
    other_confirmed = models.BooleanField(default=False, help_text="Has the Other Recipient confirmed receipt of this ER?")
    other_confirmed_on = models.DateTimeField(null=True, blank=True, help_text="When did the Other Recipient confirm?")


    receiving_facility = models.ForeignKey(Location, null=True, blank=True, help_text="The receiving facility",
                                        related_name="receiving_facility")

    requested_on = models.DateTimeField(auto_now_add=True)
    sent_response = models.BooleanField(default=False)

class AmbulanceResponse(models.Model):
    ER_RESPONSE_CHOICES = (
        ('cancelled', 'Cancelled'),
        ('arrived', 'Arrived'),
        ('pending', 'Pending')
    )

    #Note: we capture both the mom UID and try to match it to a pregnant mother foreignkey. In the event that an ER
    #is started for NOT a mother or the UID is garbled/unmatcheable we still want to capture it for analysis.
    mother_uid = models.CharField(max_length=255, help_text="Unique ID of mother", null=True, blank=True)
    mother = models.ForeignKey(PregnantMother, null=True, blank=True)
    ambulance_request = models.ForeignKey(AmbulanceRequest, null=True, blank=True)
    response = models.CharField(max_length=60, choices=ER_RESPONSE_CHOICES)


class AmbulanceOutcome(models.Model):
    ER_OUTCOME_CHOICES = (
        ('under-care', 'Under Care'),
        ('treated_discharged', 'Treated and Discharged'),
        ('deceased', 'Deceased'),
    )
    #Note: we capture both the mom UID and try to match it to a pregnant mother foreignkey. In the event that an ER
    #is started for NOT a mother or the UID is garbled/unmatcheable we still want to capture it for analysis.
    mother_uid = models.CharField(max_length=255, help_text="Unique ID of mother", null=True, blank=True)
    mother = models.ForeignKey(PregnantMother, null=True, blank=True)
    ambulance_request = models.ForeignKey(AmbulanceRequest, null=True, blank=True)
    outcome = models.CharField(max_length=60, choices=ER_OUTCOME_CHOICES)

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
    has_confirmed = models.BooleanField(default=False, help_text="Has this User confirmed their registration?")