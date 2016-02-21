# vim: ai ts=4 sts=4 et sw=4
from django.contrib.auth.models import User
from django.db import models
from rapidsms.models import Backend

from mwana.apps.locations.models import Location


class Participant(models.Model):
    SEX_CHOICES = (
        ('m', 'Male'),
        ('f', 'Female'),
    )
    phone = models.CharField(max_length=13)
    sex = models.CharField(choices=SEX_CHOICES, max_length=1, blank=True, null=True)


class PreferredBackend(models.Model):
    phone_first_part = models.CharField(max_length=6, )
    backend = models.ForeignKey(Backend)

    def __unicode__(self):
        return "%s on %s" % (self.phone_first_part, self.backend)


class Result(models.Model):
    """A viral load result"""

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

    sample_id = models.CharField(max_length=20)    #lab-assigned sample id
    requisition_id = models.CharField(max_length=50)
    payload = models.ForeignKey('Payload', null=True, blank=True,
                                related_name='test_results') # originating payload
    clinic = models.ForeignKey(Location, null=True, blank=True,
                               related_name='test_results')
    clinic_code_unrec = models.CharField(max_length=20,
                                         blank=True) #if result is for clinic not registered as a Location
    #store raw clinic code here

    result = models.CharField(max_length=30, blank=True)  #blank == 'not tested yet'
    result_unit = models.CharField(max_length=30, null=True, blank=True)
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
    sex = models.CharField(choices=SEX_CHOICES, max_length=1, blank=True)
    collecting_health_worker = models.CharField(max_length=100, blank=True)
    coll_hw_title = models.CharField(max_length=30, blank=True)
    record_change = models.CharField(choices=RECORD_CHANGE_CHOICES, max_length=6, null=True, blank=True)
    old_value = models.CharField(max_length=50, null=True, blank=True)
    verified = models.NullBooleanField(null=True, blank=True)
    result_sent_date = models.DateTimeField(null=True, blank=True)
    arrival_date = models.DateTimeField(null=True, blank=True)
    phone = models.CharField(max_length=13, blank=True, null=True)
    guspec = models.CharField(max_length=13, blank=True, null=True, verbose_name='GUSPEC')
    province = models.CharField(max_length=13, blank=True, null=True)
    district = models.CharField(max_length=13, blank=True, null=True)
    constit = models.CharField(max_length=13, blank=True, null=True)
    ward = models.CharField(max_length=13, blank=True, null=True)
    csa = models.CharField(max_length=13, blank=True, null=True)
    sea = models.CharField(max_length=13, blank=True, null=True)



    class Meta:
        ordering = ('collected_on', 'requisition_id')

    def __unicode__(self):
        return '%s - %s - %s %s (%s)' % (self.requisition_id, self.sample_id,
                                         self.clinic.slug if self.clinic else '%s[*]' % self.clinic_code_unrec,
                                         self.result if self.result else '-', self.notification_status)

    def get_result_text(self):
        return '%s%s' % (self.result, self.result_unit if self.result_unit else "")


class Payload(models.Model):
    """a raw incoming data payload from the testing lab"""

    incoming_date = models.DateTimeField()                  #date received by rapidsms
    auth_user = models.ForeignKey(User, null=True, blank=True,
                                  related_name='labtest_payloads') #http user used for authorization (blank == anon)

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
