# vim: ai ts=4 sts=4 et sw=4
import json
from datetime import datetime, timedelta, date
import logging

from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.forms import ModelForm
from django.db import transaction

from mwana.apps.labtests import models as labtests
from mwana.decorators import has_perm_or_basicauth
from mwana.apps.locations.models import Location
from django.template import RequestContext
from django.shortcuts import render_to_response



logger = logging.getLogger('mwana.apps.labtests.views')

def json_datetime (val):
    """convert a datetime value from the json into a python datetime"""
    try:
        return datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
    except:
        return None

def json_date (val):
    """convert a date value from the json into a python date"""
    try:
        return datetime.strptime(val, '%Y-%m-%d').date()
    except:
        return None

def json_timestamp (val):
    """convert a timestamp value (with milliseconds) from the json into a python datetime"""
    if val[-4] not in ('.', ','):
        return None

    try:
        dt = datetime.strptime(val[:-4], '%Y-%m-%d %H:%M:%S')
        return dt + timedelta(microseconds=1000*int(val[-3:]))
    except:
        return None


def dictval (dict, field, trans=lambda x: x, trans_none=False, default_val=None):
    """extract a value from a data dictionary, which may or may not be present in the dictionary,
    and may also need to be transformed in some way"""
    if field in dict:
        val = dict[field]
        if val is not None or trans_none:
            return trans(val)
        else:
            return None
    else:
        return default_val



@csrf_exempt
@require_http_methods(['POST'])
@has_perm_or_basicauth('labtests.add_payload', 'Lab Results')
@transaction.commit_on_success
def accept_results(request):
   
    """accept data submissions from the lab via POST."""

    if request.META['CONTENT_TYPE'] != 'text/json':
        logger.warn('incoming post does not have text/json content type')

    content = request.raw_post_data

    payload_date = datetime.now()
    payload_user = request.user
    try:
        data = json.loads(content)
    except:
        data = None
    #safety -- no matter what else happens, we'll have the original data
    payload = labtests.Payload.objects.create(incoming_date=payload_date,
                                                auth_user=payload_user,
                                                parsed_json=data is not None,
                                                raw=content)
    sid = transaction.savepoint()
    if not data:
        #if payload does not parse as valid json, save raw content and return error
        return HttpResponse('CANNOT PARSE (%d bytes received)' % len(content))
    try:
        process_payload(payload, data)
    except:
        logging.exception('second stage result parsing failed; rolling back '
                          'to savepoint.')
        transaction.savepoint_rollback(sid)
    return HttpResponse('SUCCESS')

def process_payload(payload, data=None):
    """
    Attempts to parse a payload's raw content and create the corresponding
    results in the database.
    """
    logger.debug('in process_payload')
    if data is None:
        data = json.loads(payload.raw)
    pre_record_creation = transaction.savepoint()
    #parse/save the individual result and logs entries; aggregate whether all succeeded, or if any
    #record failed to validate
    if 'samples' in data and hasattr(data['samples'], '__iter__'):
        records_validate = True
        for rec in data['samples']:
            if not accept_record(rec, payload):
                logger.debug('record %s did not validate' % rec)
                records_validate = False
    else:
        records_validate = False

    logs_validate = True #TODO: process logs
    if not (records_validate and logs_validate):
        transaction.savepoint_rollback(pre_record_creation)

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
        logger.info('saving payload %s with records_validate=%s and '
                    'logs_validate=%s' %
                    (payload, records_validate, logs_validate))
    else:
        logger.error('errors in json schema for payload %d: %s' %
                     (payload.id, str(f_payload.errors)))

def normalize_clinic_id (zpct_id):
    """turn the ZPCT clinic id format into the MoH clinic id format"""
    return zpct_id[:-1] if zpct_id[-1] == '0' and len(zpct_id) == 7 else zpct_id

def map_result (verbose_result):
    return verbose_result

def accept_record (record, payload):
    """parse and save an individual record, updating the notification flag if necessary; if record
    does not validate, nothing is saved; existing records are updated as necessary; return whether
    the record validated"""

    #retrieve existing record for id, if it exists
    sample_id = dictval(record, 'id')
    old_record = None
    if sample_id:
        try:
            old_record = labtests.Result.objects.get(sample_id=sample_id)
        except labtests.Result.DoesNotExist:
            pass

    def cant_save (message):
        message = 'cannot save record: ' + message
        if old_record:
            message += '; original record [%s] untouched' % sample_id
        message += '\nrecord: %s' % str(record)
        logger.error(message)
        logger.warning(message)

    #validate required identifying fields
    for reqd_field in ('id', 'fac'):
        if dictval(record, reqd_field) is None:
            cant_save('required field %s missing' % reqd_field)
            return False

    # If pat_id is missing, log a warning and return success without saving.
    # We can't save the record, but this is an expected error condition
    # because pat_id is not required in the source (Access) database.
    # The only way to recover is if they update the database (the record will
    # be resent at that time).
    if not dictval(record, 'pat_id'):
        logger.warning('ignoring record without pat_id field: %s' % str(record))
        return True

    #validate clinic id
    clinic_code = normalize_clinic_id(str(dictval(record, 'fac')))
    try:
        clinic_obj = Location.objects.get(slug=clinic_code)
    except Location.DoesNotExist:
        logger.warning('clinic id %s is not a recognized clinic' % clinic_code)
        clinic_obj = None

    #general field validation
    record_fields = {
        'sample_id': sample_id,
        'requisition_id': dictval(record, 'pat_id'),
        'payload': payload.id if payload else None,
        'clinic': clinic_obj.id if clinic_obj else None,
        'clinic_code_unrec': clinic_code if not clinic_obj else None,
        'result': dictval(record, 'result', map_result),
        'result_unit': dictval(record, 'unit', map_result),
        'result_detail': dictval(record, 'result_detail'),
        'collected_on': dictval(record, 'coll_on', json_date),
        'entered_on': dictval(record, 'recv_on', json_date),
        'processed_on': dictval(record, 'proc_on', json_date),
        'birthdate': dictval(record, 'dob', json_date),
        'child_age': dictval(record, 'child_age'),
        'child_age_unit': dictval(record, 'child_age_unit'),
        'sex': dictval(record, 'sex'),
        'mother_age': dictval(record, 'mother_age'),
        'collecting_health_worker': dictval(record, 'hw'),
        'coll_hw_title': dictval(record, 'hw_tit'),
        'verified': dictval(record, 'verified'),
    }

    #need to keep old record 'pristine' so we can check which fields have changed
    old_record_copy = labtests.Result.objects.get(sample_id=sample_id) if old_record else None
    f_result = ResultForm(record_fields, instance=old_record_copy)
    if f_result.is_valid():
        new_record = f_result.save(commit=False)
    else:
        cant_save('validation errors in record: %s' % str(f_result.errors))
        return False

    #validate record sync status (couldn't validate using the form because has no
    #direct analogue in the model)
    rec_status = dictval(record, 'sync')
    if rec_status not in ('new', 'update'):
        cant_save('sync_status not an allowed value')
        return False
    if new_record.result:
        # @type new_record Result
        if new_record.verified is None or new_record.verified == True:
            new_record.arrival_date = new_record.payload.incoming_date
    if not old_record:
        if rec_status == 'update':
            logger.info('received a record update for a result that doesn\'t exist in the model; original record may not have validated; treating as new record...')

        new_record.notification_status = 'new' if new_record.result else 'unprocessed'        
    else:
        #keep track of original date for payload with result
        if old_record.arrival_date and old_record.result:
            new_record.arrival_date = old_record.arrival_date

        # if result was previously sent update new record with result_sent_date
        if old_record.result_sent_date:
            new_record.result_sent_date = old_record.result_sent_date

        if rec_status == 'new':
            logger.info('received a \'new\' record that already exists; may have been deleted in lab?; treating as update...')

        new_record.notification_status = old_record.notification_status

        #change to requisition id
        if old_record.notification_status == 'sent' and old_record.requisition_id != new_record.requisition_id:
            new_record.record_change = 'req_id'
            new_record.old_value = old_record.requisition_id
            new_record.notification_status = 'updated'
            logger.warning('requisition id in record [%s] has changed (%s -> %s)! how do we handle this?' %
                           (sample_id, old_record.requisition_id, new_record.requisition_id))

        #change to clinic
        if old_record.notification_status == 'sent' and old_record.clinic != new_record.clinic:
            same_result = (new_record.result == old_record.result)
            same_patient_id = (new_record.requisition_id == old_record.requisition_id)
            if same_patient_id and same_result:
                new_record.record_change = 'loc_st'
                new_record.old_value = "%s" % (old_record.clinic.id)
                new_record.notification_status = 'new'
                logger.error('clinic id in record [%s] has changed (%s:%s -> %s:%s)!' %
                           (sample_id, old_record.clinic.slug, old_record.clinic.name, new_record.clinic.slug, new_record.clinic.name))
            elif not same_patient_id:
                new_record.record_change = 'loc_st'
                new_record.old_value = "%s" % (old_record.clinic.id)
                new_record.notification_status = 'new'
                new_record.result_sent_date = None
                logger.error('clinic & patient IDs in record [%s] have changed (%s:%s -> %s:%s) (%s -> %s)!' %
                           (sample_id, old_record.clinic.slug, old_record.clinic.name,
                           new_record.clinic.slug, new_record.clinic.name,
                           old_record.requisition_id, new_record.requisition_id))
            elif not same_result:
                new_record.record_change = 'loc_st'
                new_record.old_value = "%s" % (old_record.clinic.id)
                new_record.notification_status = 'new'
                logger.error('clinic & result in record [%s] have changed (%s:%s -> %s:%s) (%s -> %s)!' %
                           (sample_id, old_record.clinic.slug, old_record.clinic.name,
                           new_record.clinic.slug, new_record.clinic.name,
                           old_record.result, new_record.result))
        if old_record.notification_status == 'notified' and old_record.clinic != new_record.clinic:
           logger.error('clinic id for notified sample in record [%s] has changed (%s -> %s)! how do we handle this?' %
                           (sample_id, old_record.clinic.slug, new_record.clinic.slug))

        #change to test result
        if not old_record.result and new_record.result:
            new_record.notification_status = 'new'   #sample was processed by lab
        elif old_record.notification_status == 'sent' and old_record.result != new_record.result:
            logger.info('already-sent result for record [%s] has changed! need to notify of update' % sample_id)
            if not (new_record.record_change and new_record.record_change == 'loc_st'):
                new_record.notification_status = 'updated'
        #what to do if result changes from a reportable status (+, -, rej) to unreportable (indet, blank)??
            if (old_record.result in 'PN' or new_record.result in 'PN') \
            and (new_record.record_change == 'req_id' or (not new_record.record_change)):
                if not new_record.record_change: #if requisition id hasn't changed
                    new_record.record_change = 'result'
                    new_record.old_value = old_record.result
                elif new_record.record_change == 'req_id': #both requisition id and result have changed
                    new_record.record_change = 'both'
                    new_record.old_value = old_record.requisition_id + ":" + old_record.result


    new_record.save()
    return True



class PayloadForm(ModelForm):
    class Meta:
        model = labtests.Payload
        fields = ['version', 'source', 'client_timestamp', 'info']

class LogForm(ModelForm):
    class Meta:
        model = labtests.LabLog
        fields = ['timestamp', 'message', 'level', 'line']

class ResultForm(ModelForm):
    class Meta:
        model = labtests.Result
        exclude = ['notification_status','record_change','old_value',
                   'requisition_id_search']

log_rotation_threshold = 5000

def log_cmp (a, b, wraparound):
    def get_line (lg):
        ln = lg['line']
        if wraparound and ln != -1 and ln < log_rotation_threshold / 2:
            ln += 1000000
        return ln

    line_a = get_line(a)
    line_b = get_line(b)
    result = cmp(line_a, line_b)
    if result != 0:
        return result

    ts_a = a['timestamp']
    ts_b = b['timestamp']
    return cmp(ts_a, ts_b)


def level_abbr (level):
    return level[0] if level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] else level

