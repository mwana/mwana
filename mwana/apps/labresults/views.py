import json
from datetime import datetime, date, timedelta
import logging

from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.forms import ModelForm

from mwana.apps.labresults import models as labresults
from mwana.decorators import has_perm_or_basicauth

from rapidsms.contrib.locations.models import Location

def json_datetime (val):
    try:
        return datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
    except:
        return None
    
def json_date (val):
    try:
        return date.strptime(val, '%Y-%m-%d')
    except:
        return None

def json_timestamp (val):
    if val[-4] in ('.', ','):
        return None
    
    try:
        dt = datetime.strptime(val[:-4], '%Y-%m-%d %H:%M:%S')
        return dt + timedelta(microseconds=1000*int(val[-3:]))
    except:
        return None

def dictval (dict, val, trans=lambda x: x):
    return trans(dict[val]) if val in dict else None

@require_http_methods(['POST'])
@has_perm_or_basicauth('labresults.add_rawresult', 'Lab Results')
def accept_results(request):
    """Accepts incoming results from the lab via HTTP POST.  see
    connection() in extract.py for how to submit"""
    logger = logging.getLogger('mwana.apps.labresults.views.accept_results')
    
    if request.META['CONTENT_TYPE'] != 'text/json':
        logger.warn('incoming post does not have text/json content type')
    
    content = request.raw_post_data
    
    payload_date = datetime.now()
    payload_user = request.user
    try:
        data = json.loads(content)
    except:
        #if payload does not parse as valid json, save raw content and return error
        payload = labresults.Payload(incoming_date=payload_date,
                                     auth_user=payload_user,
                                     parsed_json=False,
                                     raw=content)
        payload.save()
        return HttpResponse('CANNOT PARSE (%d bytes received)' % len(content))
    
    #safety -- no matter what else happens, we'll have the original data
    payload = labresults.Payload(incoming_date=payload_date,
                                 auth_user=payload_user,
                                 parsed_json=True,
                                 raw=content)
    try:
        payload.save()
    except:
        #failed to save raw data; attempt to leave it in the log
        logger.exception('could not save raw incoming data from DBS lab!! raw data: %s' % content)
        raise
    
    #parse/save the individual result and logs entries; aggregate whether all succeeded, or if any
    #record failed to validate
    records_validate = all(accept_record(r) for r in data['records']) if 'records' in data else False
    logs_validate = all(accept_log(l, payload.id) for l in data['logs']) if 'logs' in data else False
    
    meta_fields = {
        'version': dictval(data, 'version'),
        'source': dictval(data, 'source'), 
        'client_timestamp': dictval(data, 'now', json_datetime),
        'info':  dictval(data, 'info'),
    }
    
    f_payload = PayloadForm(meta_fields, instance=payload)
    if f_payload.is_valid():
        payload = f_payload.save(commit=False)
        payload.validated_schema = (records_validate and logs_validate)
        payload.save()
    else:
        logger.error('errors in json schema for payload: ' + str(f_payload.errors))
                
    return HttpResponse('SUCCESS')
     
def normalize_clinic_id (zpct_id):
    return zpct_id[:-1] if zpct_id[-1] == '0' and len(zpct_id) > 3 else zpct_id
     
def map_result (verbose_result):
    result_codes = {'positive': 'P',
                    'negative': 'N',
                    'rejected': 'R',
                    'indeterminate': 'I',
                    'inconsistent': 'X'}
    return result_codes[verbose_result] if verbose_result in result_codes else ('x-' + verbose_result)
     
def accept_record (record):
    logger = logging.getLogger('mwana.apps.labresults.views.accept_record')
    
    #retrieve existing record for id, if it exists
    sample_id = dictval(record, 'id')
    old_record = None
    if sample_id != None:
        try:
            old_record = labresults.Result.objects.get(sample_id=sample_id)
        except labresults.Result.DoesNotExist:
            pass
    
    def cant_save (message):
        message = 'cannot save record: ' + message
        if old_record != None:
            message += '; original record [%s] untouched' % sample_id
        message += '\nrecord: %s' % str(record)
        logger.error(message)
    
    #validate required identifying fields
    for reqd_field in ('id', 'pat_id', 'fac'):
        if dictval(record, reqd_field) == None:
            cant_save('required field %s missing' % reqd_field)
            return False
    
    #validate clinic id
    clinic_id = normalize_clinic_id(dictval(record, 'fac'))
    try:
        clinic_obj = Location.objects.get(slug=clinic_id)
    except Location.DoesNotExist:
        cant_save('clinic id %s is not a recognized clinic' % clinic_id)
        return False
        
    #general field validation
    record_fields = {
        'sample_id': sample_id,
        'requisition_id': dictval(record, 'pat_id'),
        'clinic': clinic_obj,
        'result': dictval(record, 'result', map_result),
        'result_detail': dictval(record, 'result_detail'),
        'collected_on': dictval(record, 'coll_on', json_date),
        'entered_on': dictval(record, 'recv_on', json_date),
        'processed_on': dictval(record, 'proc_on', json_date),
        'birthdate': dictval(record, 'dob', json_date),
        'child_age': dictval(record, 'child_age'),
        'sex': dictval(record, 'sex'),
        'mother_age': dictval(record, 'mother_age'),
        'collecting_health_worker': dictval(record, 'hw'),
        'coll_hw_title': dictval(record, 'hw_tit'),
    }
    f_result = ResultForm(record_fields)
    if f_result.is_valid():
        new_record = f_result.save(commit=False)
    else:
        cant_save('validation errors in record: %s' % str(f_result.errors))
        return False

    #validate record sync status (couldn't validate with the rest of the fields because has no
    #direct analogue in the model)
    rec_status = dictval(record, 'sync')
    if rec_status not in ('new', 'update'):
        cant_save('sync_status not an allowed value')
        return False

    if old_record == None:
        if rec_status == 'update':
            logger.info('received a record update for a result that doesn\'t exist in the model; original record may not have validated; treating as new record...')
        
        new_record.notification_status = 'new' if new_record.result != None else 'unprocessed'
    else:
        new_record.notification_status = old_record.notification_status

        #change to requisition id
        if old_record.notification_status == 'sent' and old_record.requisition_id != new_record.requisition_id:
            logger.warning('requisition id in record [%s] has changed (%s -> %s)! how do we handle this?' %
                           (sample_id, old_record.requisition_id, new_record.requisition_id))

        #change to clinic
        if old_record.notification_status in ('sent', 'notified') and old_record.clinic != new_record.clinic:
            logger.warning('clinic id in record [%s] has changed (%s -> %s)! how do we handle this?' %
                           (sample_id, old_record.clinic.slug, new_record.clinic.slug))

        #change to test result
        if old_record.result == None and new_record.result != None:
            new_record.notification_status = 'new'   #sample was processed by lab
        elif old_record.notification_status == 'sent' and old_record.result != new_record.result:
            logger.info('already-sent result for record [%s] has changed! need to notify of update' % sample_id)
            new_record.notification_status = 'updated'
                
    new_record.save()
    return True
    


def accept_log (log, payload_id):
    logger = logging.getLogger('mwana.apps.labresults.views.accept_log')
    
    logentry = labresults.LabLog(payload_id=payload_id)

    logfields = {
        'timestamp': dictval(log, 'at', json_timestamp),
        'message': dictval(log, 'msg'),
        'level': dictval(log, 'lvl'),
        'line': dictval(log, 'ln')
    }

    f_log = LogForm(logfields, instance=logentry)
    if f_log.is_valid():
        f_log.save()
        return True
    else:
        logger.error('errors in json schema for log: ' + str(f_log.errors))
        logentry.raw = str(log)
        logentry.save()
        return False
     

class PayloadForm(ModelForm):
    class Meta:
        model = labresults.Payload
        fields = ['version', 'source', 'client_timestamp', 'info']

class LogForm(ModelForm):
    class Meta:
        model = labresults.LabLog
        fields = ['timestamp', 'message', 'level', 'line']
        
class ResultForm(ModelForm):
    class Meta:
        model = labresults.Result
        exclude = ['notification_status']
        