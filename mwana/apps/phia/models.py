# vim: ai ts=4 sts=4 et sw=4
from django.contrib.auth.models import User
from django.db import models
from rapidsms.models import Contact
from datetime import datetime

from mwana.apps.locations.models import Location
import base64


class Result(models.Model):

    RECORD_CHANGE_CHOICES = (
        ('result', 'Result changed'),
        ('req_id', 'Requisition ID changed'),
        ('both', 'Both the result and requisition id changed'),
        ('loc_st', 'Location changed after sending result')
    )

    STATUS_CHOICES = (
        ('in-transit', 'En route to lab'), #not supported currently
        ('unprocessed', 'At lab, not processed yet'),
        ('new', 'Fresh result from lab'),
        ('notified', 'Clinic notified of new result'),
        ('sent', 'Result sent to clinic'),
        ('updated', 'Updated data from lab'),
        ('obsolete', 'Obsolete') # As good as deleted on the Mwana server but kept for reference sake
    )

    SEX_CHOICES = (
        ('m', 'Male'),
        ('f', 'Female'),
    )

    _fname = models.TextField(
        db_column='fname_data', editable=False,
        blank=True)

    def set_fname(self, fname):
        if fname:
            self._fname = base64.encodestring(fname)

    def get_fname(self):
        return base64.decodestring(self._fname)

    fname = property(get_fname, set_fname)
    _lname = models.TextField(
        db_column='lname_data', editable=False,
        blank=True)

    def set_lname(self, lname):
        if lname:
            self._lname = base64.encodestring(lname)

    def get_lname(self):
        return base64.decodestring(self._lname)

    lname = property(get_lname, set_lname)
    _nick_name = models.TextField(
        db_column='nick_name_data', editable=False,
        blank=True)

    def set_nick_name(self, nick_name):
        if nick_name:
            self._nick_name = base64.encodestring(nick_name)

    def get_nick_name(self):
        return base64.decodestring(self._nick_name)

    nick_name = property(get_nick_name, set_nick_name)
    _phone = models.TextField(
        db_column='phone_data', editable=False,
        blank=True)

    def set_phone(self, phone):
        if phone:
            self._phone = base64.encodestring(phone)

    def get_phone(self):
        return base64.decodestring(self._phone)

    phone = property(get_phone, set_phone)
    _address = models.TextField(
        db_column='address_data', editable=False,
        blank=True)

    def set_address(self, address):
        if address:
            self._address = base64.encodestring(address)

    def get_address(self):
        return base64.decodestring(self._address)

    address = property(get_address, set_address)

    sex = models.CharField(choices=SEX_CHOICES, max_length=1, blank=True, null=True)

    age = models.PositiveSmallIntegerField(null=True, blank=True)
    send_pii = models.NullBooleanField(null=True, blank=True)
    share_contact = models.NullBooleanField(null=True, blank=True)
    contact_by_phone = models.NullBooleanField(null=True, blank=True)
    fa_code = models.CharField(max_length=20, null=True, blank=True)
    fa_name = models.CharField(max_length=100, null=True, blank=True)
    contact_method = models.CharField(max_length=30, null=True, blank=True)

    sample_id = models.CharField(max_length=20)    #lab-assigned sample id
    requisition_id = models.CharField(max_length=50)
    payload = models.ForeignKey('Payload', null=True, blank=True) # originating payload
    clinic = models.ForeignKey(Location, null=True, blank=True, related_name='phia_results')
    clinic_code_unrec = models.CharField(max_length=20,  blank=True) #if result is for clinic not registered as a Location
    given_facility_name = models.CharField(max_length=100,blank=True, null=True)
    given_facility_code = models.CharField(max_length=100, blank=True, null=True)

    result_detail = models.CharField(max_length=200, blank=True)   #reason for rejection or explanation of inconsistency
    collected_on = models.DateField(null=True, blank=True)   #date collected at clinic
    entered_on = models.DateField(null=True, blank=True)     #date received at lab
    processed_on = models.DateField(null=True, blank=True)   #date tested at lab
    #all date fields are entered by lab -- not based on date result entered or such

    notification_status = models.CharField(choices=STATUS_CHOICES, max_length=15)

    #ancillary demographic data that can help matching up results back to patients
    birthdate = models.DateField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    age_unit = models.CharField(null=True, blank=True, max_length=20)
    collecting_health_worker = models.CharField(max_length=100, blank=True)
    coll_hw_title = models.CharField(max_length=30, blank=True)
    record_change = models.CharField(choices=RECORD_CHANGE_CHOICES, max_length=6, null=True, blank=True)
    old_value = models.CharField(max_length=50, null=True, blank=True)
    verified = models.NullBooleanField(null=True, blank=True)
    result_sent_date = models.DateTimeField(null=True, blank=True)
    date_of_first_notification = models.DateTimeField(null=True, blank=True)
    arrival_date = models.DateTimeField(null=True, blank=True)
    phone_invalid = models.CharField(max_length=20, blank=True, null=True)
    province = models.CharField(max_length=13, blank=True, null=True)
    district = models.CharField(max_length=13, blank=True, null=True)
    date_clinic_notified = models.DateTimeField(null=True, blank=True)
    date_participant_notified = models.DateTimeField(null=True, blank=True)
    who_retrieved = models.ForeignKey(Contact, null=True, blank=True,  related_name='phia_results')
    participant_informed = models.PositiveSmallIntegerField(null=True, blank=True)
    past_test = models.NullBooleanField(null=True, blank=True)
    past_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30, blank=True)
    was_on_art = models.NullBooleanField(null=True, blank=True)
    on_art = models.NullBooleanField(null=True, blank=True)
    art_start_date = models.DateField(max_length=30, blank=True, null=True)
    # contact_by_phone = models.NullBooleanField(null=True, blank=True)
    # send_pii = models.NullBooleanField(null=True, blank=True)
    # share_contact = models.NullBooleanField(null=True, blank=True)
    linked = models.BooleanField(default=False)
    # contact_method = models.CharField(max_length=30, blank=True)
    bd_date = models.DateField(null=True, blank=True)
    vl = models.CharField(max_length=30, blank=True)
    vl_date = models.DateField(null=True, blank=True)
    cd4 = models.CharField(max_length=30, blank=True)
    cd4_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ('collected_on', 'requisition_id')

    def __unicode__(self):
        return '%s - %s - %s %s (%s)' % (self.requisition_id, self.sample_id,
                                         self.clinic.slug if self.clinic else '%s[*]' % self.clinic_code_unrec,
                                         self.result if self.result else '-', self.notification_status)

    def get_result_text(self):
        return '%s;%s' % (self.cd4 or '', self.vl or '')


class Followup(models.Model):
    """ LTC Followup visits log """
    result = models.ForeignKey(Result)
    temp_id = models.CharField(max_length=50)
    clinic_name = models.CharField(max_length=100)
    reported_on = models.DateTimeField(default=datetime.now)
    reported_by = models.CharField(max_length=200)

    class Meta:
        ordering = ('reported_on', 'reported_by')

    def __unicode__(self):
        return '%s | %s | %s' % (self.temp_id, self.clinic_name,
                                self.reported_on)


class Payload(models.Model):
    """a raw incoming data payload from the testing lab"""

    incoming_date = models.DateTimeField()                  #date received by rapidsms
    auth_user = models.ForeignKey(User, null=True, blank=True,
                                  related_name='phia_payloads') #http user used for authorization (blank == anon)

    version = models.CharField(max_length=10, blank=True)    #version of extract script payload came from
    source = models.CharField(max_length=50, blank=True)     #source identifier (i.e., 'ndola')
    client_timestamp = models.DateTimeField(null=True,
                                            blank=True)      #timestamp on lab computer that payload was created
    #use to detect if lab computer clock is off
    info = models.CharField(max_length=50, blank=True)       #extra info about payload

    parsed_json = models.BooleanField(default=False)        #whether this payload parsed as valid json
    validated_schema = models.BooleanField(default=False, help_text='If parsed'
                                                                    ', whether this payload validated '
                                                                    'completely according to the '
                                                                    'expectation of our schema; if '
                                                                    'false, it is likely that some of '
                                                                    'the data in this payload did NOT '
                                                                    'make it into Result or LabLog '
                                                                    'records!')

    raw = models.TextField()        #raw POST content of the payload; will always be present, even if other fields
    #like version, source, etc., couldn't be parsed

    def __unicode__(self):
        return 'from %s::%s at %s (%s bytes)' % (self.source if self.source else '-',
                                                 self.version if self.version else '-',
                                                 self.incoming_date.strftime('%Y-%m-%d %H:%M:%S'),
                                                 len(self.raw))


class LabLog(models.Model):
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

class Linkage(models.Model):
    """2020/02/10 18:00:02
       Logs Linkage To Care of all participants even those whose results are not yet in the system.
       That may happen if participants tested have quickly gone to the clinic before lab results are ready
       It is also used to track how active HCW are to determine their remuneration
    """
    temp_id = models.CharField(max_length=50, unique=True)
    clinic = models.ForeignKey(Location, null=True, blank=True)
    clinic_code = models.CharField(max_length=20)
    linked_by = models.ForeignKey(Contact)
    linked_on = models.DateTimeField(default=datetime.now)
    result = models.ForeignKey(Result, null=True, blank=True)

    class Meta:
        ordering = ('linked_on', 'linked_by')

    def __unicode__(self):
        return '%s | %s | %s | %s' % (self.temp_id, self.clinic.name, self.clinic_code, self.linked_on)