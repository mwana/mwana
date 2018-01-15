# vim: ai ts=4 sts=4 et sw=4
from django.contrib.auth.models import User
from rapidsms.models import Connection
from django.db import models
from mwana.apps.locations.models import Location
from mwana.apps.act.messages import CLIENT_MESSAGE_CHOICES
import base64


class Payload(models.Model):
    """a raw incoming data payload"""

    incoming_date = models.DateTimeField()                  #date received by rapidsms
    auth_user = models.ForeignKey(User, null=True, blank=True,
                                  related_name='act_payloads') #http user used for authorization (blank == anon)

    version = models.CharField(max_length=10, blank=True)    #version of extract script payload came from
    source = models.CharField(max_length=50, blank=True)
    client_timestamp = models.DateTimeField(null=True, blank=True)
    info = models.CharField(max_length=50, blank=True)       #extra info about payload

    parsed_json = models.BooleanField(default=False)        #whether this payload parsed as valid json
    validated_schema = models.BooleanField(default=False, help_text='If parsed'
                                                                    ', whether this payload validated '
                                                                    'completely according to the '
                                                                    'expectation of our schema; if '
                                                                    'false, it is likely that some of '
                                                                    'the data in this payload did NOT '
                                                                    'make it into Appointment or Log '
                                                                    'records!')

    raw = models.TextField()        #raw POST content of the payload; will always be present, even if other fields
    #like version, source, etc., couldn't be parsed

    def __unicode__(self):
        return 'from %s::%s at %s (%s bytes)' % (self.source if self.source else '-',
                                                 self.version if self.version else '-',
                                                 self.incoming_date.strftime('%Y-%m-%d %H:%M:%S'),
                                                 len(self.raw))


class Log(models.Model):
    """a logging message from the lab computer extract script"""

    timestamp = models.DateTimeField(null=True, blank=True)
    message = models.TextField(blank=True)
    level = models.CharField(max_length=20, blank=True)
    line = models.IntegerField(null=True, blank=True)

    payload = models.ForeignKey(Payload)       #payload this message came from
    raw = models.TextField(blank=True) #raw content of log -- present only if log info couldn't be
    #parsed/validated

    def __unicode__(self):
        return ('%s: %s> %s' % (self.line, self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                self.message if len(self.message) < 20 else (self.message[:17] + '...'))) \
            if not self.raw else 'parse error'


class CHW(models.Model):
    name = models.CharField(max_length=255)
    national_id = models.CharField(max_length=255)
    address = models.TextField(null=True, blank=True)
    location = models.ForeignKey(Location, null=True, blank=True)
    clinic_code_unrec = models.CharField(max_length=10, null=True, blank=True)
    phone = models.CharField(max_length=13, null=True, blank=True)
    phone_verified = models.NullBooleanField(null=True, blank=True, default=False)
    uuid = models.CharField(max_length=255, unique=True)
    connection = models.ForeignKey(Connection, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


GENDER_CHOICES = (
    ('m', 'Male'),
    ('f', 'Female'),
)


class Client(models.Model):
    _name = models.TextField(
        db_column='data',
        blank=True)

    def set_name(self, name):
        self._name = base64.encodestring(name)

    def get_name(self):
        return base64.decodestring(self._name)

    name = property(get_name, set_name)
    national_id = models.CharField(max_length=255, unique=True)
    alias = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField(null=True, blank=True)
    short_address = models.TextField(null=True, blank=True)
    can_receive_messages = models.NullBooleanField()  # Client consented to receiving SMS messages
    location = models.ForeignKey(Location, null=True, blank=True)
    clinic_code_unrec = models.CharField(max_length=10, null=True, blank=True)
    zone = models.CharField(max_length=20, null=True, blank=True)
    phone = models.CharField(max_length=13, null=True, blank=True)
    phone_verified = models.NullBooleanField(null=True, blank=True, default=False)
    uuid = models.CharField(max_length=255, unique=True)
    connection = models.ForeignKey(Connection, null=True, blank=True)
    community_worker = models.ForeignKey(CHW, blank=True, null=True)

    def __unicode__(self):
        return self.alias

    def is_eligible_for_messaging(self):
        return self.can_receive_messages and self.phone_verified and (self.connection is not None)


class FlowCHWRegistration(models.Model):
    name = models.CharField(max_length=255)
    national_id = models.CharField(max_length=255)
    address = models.TextField(null=True, blank=True)
    location = models.ForeignKey(Location, null=True, blank=True)
    open = models.BooleanField(default=True)
    start_time = models.DateTimeField(editable=False)
    valid_until = models.DateTimeField(editable=False)
    connection = models.ForeignKey(Connection, editable=False)

    def __unicode__(self):
        return self.name


class FlowClientRegistration(models.Model):
    national_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=1, choices=GENDER_CHOICES)
    can_receive_messages = models.NullBooleanField()  # Client consented to receiving SMS messages
    phone = models.CharField(max_length=13, null=True, blank=True)
    open = models.BooleanField(default=True)
    start_time = models.DateTimeField(editable=False)
    valid_until = models.DateTimeField(editable=False)
    community_worker = models.ForeignKey(CHW, blank=True, null=True)


LAB_TYPE = 'lab'
PHARMACY_TYPE = 'pharmacy'
APPOINTMENT_TYPES = (
    (LAB_TYPE, 'Lab Visit'),
    (PHARMACY_TYPE, 'Pharmacy Visit')
)


class FlowAppointment(models.Model):
    open = models.BooleanField(default=True)
    start_time = models.DateTimeField(editable=False)
    valid_until = models.DateTimeField(editable=False)
    date = models.DateField(null=True, blank=True)
    type = models.CharField(choices=APPOINTMENT_TYPES, max_length=10, null=True, blank=True)
    message_id = models.CharField(max_length=2, null=True, blank=True)
    client = models.ForeignKey(Client, null=True, blank=True)
    community_worker = models.ForeignKey(CHW, blank=True, null=True)


class Appointment(models.Model):
    APPOINTMENT_STATUS = (
        ('pending', 'Pending'),
        ('attended', 'Attended'),
        ('notified', 'Notified by SMS'),
        ('missed', 'Missed'),
        ('canceled', 'Canceled'),
    )

    client = models.ForeignKey(Client)
    cha_responsible = models.ForeignKey(CHW, null=True, blank=True)
    type = models.CharField(choices=APPOINTMENT_TYPES, max_length=10)
    date = models.DateField(help_text="Date when client should go to clinic for this appointment")
    status = models.CharField(choices=APPOINTMENT_STATUS, max_length=10, default='pending')
    notes = models.CharField(max_length=255, blank=True, null=True)
    payload = models.ForeignKey(Payload, null=True, blank=True)
    uuid = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return "%s on %s for %s" % (self.client, self.date, self.type)

    @classmethod
    def get_lab_type(cls):
        return LAB_TYPE

    @classmethod
    def get_pharmacy_type(cls):
        return PHARMACY_TYPE

    def is_lab_type(self):
        return self.type == LAB_TYPE

    def is_pharmacy_type(self):
        return self.type == PHARMACY_TYPE


class VerifiedNumber(models.Model):
    number = models.CharField(max_length=13)
    verified = models.BooleanField(default=True)

    def __unicode__(self):
        return "%s. Verified: %s" % (self.number, self.verified)


class ReminderDay(models.Model):
    #TODO: in case the period for collection of drugs has been reduced, ensure only valid reminders go
    appointment_type = models.CharField(choices=APPOINTMENT_TYPES, max_length=10)
    days = models.PositiveSmallIntegerField(help_text='Number of days before appointment date when reminder is sent')
    activated = models.BooleanField(default=True)

    def __unicode__(self):
        return "%s at %s days" % (self.get_appointment_type_display(), self.days)

    class Meta:
        unique_together = (('appointment_type', 'days',),)


class SentReminder(models.Model):
    appointment = models.ForeignKey(Appointment)
    reminder_type = models.ForeignKey(ReminderDay)
    phone = models.CharField(max_length=13)
    date_logged = models.DateTimeField(auto_now_add=True)
    visit_date = models.DateField()  # If appointment date is updated reminder has to be sent again

    def __unicode__(self):
        return "%s Reminder for appointment %s on %s" % (self.reminder_type, self.appointment, self.date_logged)

    class Meta:
        unique_together = ('appointment', 'reminder_type', 'phone')


class RemindersSwitch(models.Model):
    """
    Sometimes we need to turn of reminders temporally
    """
    can_send_reminders = models.BooleanField(default=True)
    logged_on = models.DateField(auto_now=True)
    singleton_lock = models.SmallIntegerField(choices=((1, 'lock'),), default=1, unique=True, null=False, blank=False)

    def __unicode__(self):
        return "%s send reminders" % ("Can" if self.can_send_reminders else "Can NOT")


class SystemUser(models.Model):
    name = models.CharField(max_length=255)
    password_slice = models.CharField(max_length=255)
    site = models.CharField(max_length=255)

    def __unicode__(self):
        return "%s of %s" % (self.name, self.site)


class HistoricalEvent(models.Model):
    date = models.DateField()#TODO: ensure date is >= 1900. Add unique together
    fact_message = models.CharField(max_length=120)

    def __unicode__(self):
        return 'Did you know? On %s %s' % (self.date.strftime('%d %B'), self.fact_message)

    def did_you_know_message(self):
        return 'Did you know? On %s %s' % (self.date.strftime('%d %B'), self.fact_message)

    @classmethod
    def mock_message(cls, p_date):
        return 'Happy healthy day %s' % (p_date.strftime('%d %B'))


class ReminderMessagePreference(models.Model):
    client = models.ForeignKey(Client)
    message_id = models.CharField(max_length=5, choices=CLIENT_MESSAGE_CHOICES.items())
    visit_type = models.CharField(choices=APPOINTMENT_TYPES, max_length=10)

    def __unicode__(self):
        return "%s => %s: %s" % (self.client, self.visit_type, self.message_id)

    class Meta:
        unique_together = (('client', 'visit_type',),)

    def get_message_text(self):
        return CLIENT_MESSAGE_CHOICES.get(self.message_id)