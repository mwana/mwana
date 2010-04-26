from django.db import models
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Connection
from django.contrib.auth.models import User

class Result(models.Model):
    RESULT_CHOICES = (
        ('P', 'HIV Positive'),
        ('N', 'HIV Negative'),
        ('R', 'Rejected Sample'),   #this could include samples that failed to give a definitive result
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

    sample_id = models.CharField(primary_key=True, max_length=10)    #lab-assigned sample id
    requisition_id = models.CharField(max_length=50)   #non-standardized format varying by clinic; could be patient
                                                       #id, clinic-assigned sample id, or even patient name
    clinic = models.ForeignKey(Location)

    result = models.CharField(choices=RESULT_CHOICES, max_length=1, null=True)  #null == 'not tested yet'
    result_detail = models.CharField(max_length=200, null=True)   #reason for rejection or explanation of inconsistency
    
    collected_on = models.DateField(null=True)   #date collected at clinic
    entered_on = models.DateField(null=True)     #date received at lab
    processed_on = models.DateField(null=True)   #date tested at lab
    #all date fields are entered by lab -- not based on date result entered or such
    
    notification_status = models.CharField(choices=STATUS_CHOICES, max_length=15)

    #ancillary demographic data that can help matching up results back to patients
    birthdate = models.DateField(null=True)
    child_age = models.IntegerField(null=True)  #age in weeks
    sex = models.CharField(choices=SEX_CHOICES, max_length=1, null=True)
    mother_age = models.IntegerField(null=True) #age in years
    collecting_health_worker = models.CharField(max_length=100, null=True)
    coll_hw_title = models.CharField(max_length=30, null=True)

    def __unicode__(self):
        return '%s/%s/%s %s (%s)' % (self.requisition_id, self.sample_id, self.clinic.slug,
                                     self.result if self.result != None else '-', self.notification_status)


class Payload(models.Model):
    incoming_date = models.DateTimeField()
    auth_user = models.ForeignKey(User)
    
    version = models.CharField(max_length=10, null=True)
    source = models.CharField(max_length=50, null=True)
    client_timestamp = models.DateTimeField(null=True)
    info = models.CharField(max_length=50, null=True)
    
    parsed_json = models.BooleanField(default=False)
    validated_schema = models.BooleanField(default=False)
    
    raw = models.TextField()
    
    def __unicode__(self):
        return 'from %s/%s at %s (%sb)' % (self.source if self.source != None else '-',
                                           self.version if self.version != None else '-',
                                           self.incoming_date.strftime('%Y-%m-%d %H:%M:%S'),
                                           len(self.raw))

class LabLog(models.Model):
    timestamp = models.DateTimeField(null=True)
    message = models.TextField(null=True)
    level = models.CharField(max_length=20, null=True)
    line = models.IntegerField(null=True)
    
    payload_id = models.ForeignKey(Payload)
    raw = models.TextField(null=True)
    
    def __unicode__(self):
        return ('%d: %s> %s' % (self.line, self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                self.message if len(self.message) < 20 else (self.message[:17] + '...'))) \
            if self.raw != None else 'parse error'