from django.contrib.auth.models import User
from django.db import models
from datetime import datetime
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Connection, Contact


class SampleNotification(models.Model):
    """
    Records notifications that samples were sent.  This class
    is not linked to the Result class because we don't have 
    individual sample ids, so we just include them in bulk.
    """
    
    contact  = models.ForeignKey(Contact)
    location = models.ForeignKey(Location)
    count    = models.PositiveIntegerField()
    count_in_text = models.CharField(max_length=160, null=True, blank = True)
    date     = models.DateTimeField(default=datetime.utcnow)
    
    def __unicode__(self):
        "%s DBS Samples from %s on %s" % \
            (self.count, self.location, self.date.date())

class Result(models.Model):
    """a DBS result, including patient tracking info, actual result, and status
    of sending result back to clinic"""
    
    RESULT_CHOICES = (
        ('P', 'Detected'),
        ('N', 'NotDetected'),
        ('R', 'Rejected'),   #this could include samples that failed to give a definitive result
                                    #  i.e., 'rejected -- indeterminate'
        ('I', 'Indeterminate'),     #could mean 'unable to get definitive result', but most likely means
                                    #  'sample on hold while we investigate missing critical data, such
                                    #  as originating facility'; if data cannot be found, sample will be
                                    #  ultimately rejected. we should sit on these for a while before we
                                    #  send them out
        ('X', 'Inconsistent'),      #means the source database has record in a state that doesn't make
                                    #  sense; sit on it indefinitely, hoping it will resolve to a
                                    #  different status
    )
    
    def get_result(self):
        if self.result in ('X', 'I'):
            return 'Rejected'
        else:
            return super(Result, self).get_result_display()

    STATUS_CHOICES = (
        ('in-transit', 'En route to lab'),      #not supported currently
        ('unprocessed', 'At lab, not processed yet'),
        ('new', 'Fresh result from lab'),
        ('notified', 'Clinic notified of new result'),
        ('sent', 'Result sent to clinic'),
        ('updated', 'Updated data from lab')    #set when server receives updates to a sample record
                                                #AFTER this result has already been sent to the clinic.
                                                #if result has not yet been sent, it keeps status 'new'.
                                                #the updated data may or may not merit sending the
                                                #update to the clinic (i.e., changed result, yes, changed
                                                #child age, no)
    )

    SEX_CHOICES = (
        ('m', 'Male'),
        ('f', 'Female'),
    )

    AGE_UNIT_CHOICES = (
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years'),
    )
    sample_id = models.CharField(max_length=10)    #lab-assigned sample id
    requisition_id = models.CharField(max_length=50)   #non-standardized format varying by clinic; could be patient
                                                       #id, clinic-assigned sample id, or even patient name
    payload = models.ForeignKey('Payload', null=True, blank=True,
                                related_name='lab_results') # originating payload
    clinic = models.ForeignKey(Location, null=True, blank=True,
                               related_name='lab_results')
    clinic_code_unrec = models.CharField(max_length=20, blank=True) #if result is for clinic not registered as a Location
                                                                    #store raw clinic code here

    result = models.CharField(choices=RESULT_CHOICES, max_length=1, blank=True)  #blank == 'not tested yet'
    result_detail = models.CharField(max_length=200, blank=True)   #reason for rejection or explanation of inconsistency
    
    collected_on = models.DateField(null=True, blank=True)   #date collected at clinic
    entered_on = models.DateField(null=True, blank=True)     #date received at lab
    processed_on = models.DateField(null=True, blank=True)   #date tested at lab
    #all date fields are entered by lab -- not based on date result entered or such
    
    notification_status = models.CharField(choices=STATUS_CHOICES, max_length=15)

    #ancillary demographic data that can help matching up results back to patients
    birthdate = models.DateField(null=True, blank=True)
    child_age = models.IntegerField(null=True, blank=True)
    child_age_unit = models.CharField(null=True, blank=True, max_length=20,
                                      choices=AGE_UNIT_CHOICES)
    sex = models.CharField(choices=SEX_CHOICES, max_length=1, blank=True)
    mother_age = models.IntegerField(null=True, blank=True) #age in years
    collecting_health_worker = models.CharField(max_length=100, blank=True)
    coll_hw_title = models.CharField(max_length=30, blank=True)
    verified = models.NullBooleanField(null=True, blank=True)

    class Meta:
        ordering = ('collected_on', 'requisition_id')

    def __unicode__(self):
        return '%s - %s - %s %s (%s)' % (self.requisition_id, self.sample_id,
                                         self.clinic.slug if self.clinic else '%s[*]' % self.clinic_code_unrec,
                                         self.result if self.result else '-', self.notification_status)


class Payload(models.Model):
    """a raw incoming data payload from the DBS lab computer"""
    
    incoming_date = models.DateTimeField()                  #date received by rapidsms
    auth_user = models.ForeignKey(User, null=True, blank=True) #http user used for authorization (blank == anon)
    
    version = models.CharField(max_length=10, blank=True)    #version of extract script payload came from
    source = models.CharField(max_length=50, blank=True)     #source identifier (i.e., 'ndola')
    client_timestamp = models.DateTimeField(null=True, blank=True)      #timestamp on lab computer that payload was created
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
