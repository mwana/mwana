# vim: ai ts=4 sts=4 et sw=4
import json
from datetime import datetime, timedelta, date
import logging

from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.forms import ModelForm
from django.db import transaction

from mwana.apps.labresults import models as labresults
from mwana.decorators import has_perm_or_basicauth
from mwana.apps.locations.models import Location
from django.template import RequestContext
from django.shortcuts import render_to_response

"""
TODO

* write unit tests / fix existing unit tests
* write a migration
  - this migration should also parse the raw json that has been sent but unprocessed since friday april 23
    - note that this json is from a different version of the script, so some fields will differ
      slightly (Payload.version, Payload.info, and LabLog.line -- all missing)
* rectify the current facility list with the ndola lab facility list (the lab list contains the facilities of
  all provinces it services; our list only contains luapula. it is not required from incoming results to have
  a facility in our list -- you can still save the result record, but not send it. however, it appeared that
  the lab list even had a few luapula clinics that aren't on our internal list
"""

logger = logging.getLogger('mwana.apps.labresults.views')

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


@require_GET
def dashboard(request):
    locations = Location.objects.all()
    return render_to_response("labresults/dashboard.html",
                              {"locations": locations },context_instance=RequestContext(request))


@csrf_exempt
@require_http_methods(['POST'])
@has_perm_or_basicauth('labresults.add_payload', 'Lab Results')
@transaction.commit_on_success
def accept_results(request):
    """accept data submissions from the lab via POST. see connection() in extract.py
    for how to submit; attempts to save raw data/partial data if for some reason the
    full content is not parseable or does not validate to the model schema"""

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
    payload = labresults.Payload.objects.create(incoming_date=payload_date,
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

    if 'logs' in data and hasattr(data['logs'], '__iter__'):
        logs_validate = True
        for log in data['logs']:
            if not accept_log(log, payload):
                logger.debug('log %s did not validate' % log)
                logs_validate = False
    else:
        logger.debug('no logs in data')
        logs_validate = False

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
    """map the result type from extract.py codes to Result model codes"""
    result_codes = {'positive': 'P',
                    'negative': 'N',
                    'rejected': 'R',
                    'indeterminate': 'I',
                    'inconsistent': 'X'}
    return result_codes[verbose_result] if verbose_result in result_codes else ('x-' + verbose_result)

def accept_record (record, payload):
    """parse and save an individual record, updating the notification flag if necessary; if record
    does not validate, nothing is saved; existing records are updated as necessary; return whether
    the record validated"""

    #retrieve existing record for id, if it exists
    sample_id = dictval(record, 'id')
    old_record = None
    if sample_id:
        try:
            old_record = labresults.Result.objects.get(sample_id=sample_id)
        except labresults.Result.DoesNotExist:
            pass

    def cant_save (message):
        message = 'cannot save record: ' + message
        if old_record:
            message += '; original record [%s] untouched' % sample_id
        message += '\nrecord: %s' % str(record)
        logger.error(message)

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
        'clinic_care_no': dictval(record, 'clinic_care_no'),
    }

    #need to keep old record 'pristine' so we can check which fields have changed
    old_record_copy = labresults.Result.objects.get(sample_id=sample_id) if old_record else None
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
        if old_record.notification_status in ('sent', 'notified') and old_record.clinic != new_record.clinic:
            logger.warning('clinic id in record [%s] has changed (%s -> %s)! how do we handle this?' %
                           (sample_id, old_record.clinic.slug, new_record.clinic.slug))

        #change to test result
        if not old_record.result and new_record.result:
            new_record.notification_status = 'new'   #sample was processed by lab
        elif old_record.notification_status == 'sent' and old_record.result != new_record.result:
            logger.info('already-sent result for record [%s] has changed! need to notify of update' % sample_id)
            new_record.notification_status = 'updated'
        #what to do if result changes from a reportable status (+, -, rej) to unreportable (indet, blank)??
            if old_record.result in 'PN' or new_record.result in 'PN':
                if not new_record.record_change: #if requisition id hasn't changed
                    new_record.record_change = 'result'
                    new_record.old_value = old_record.result
                else: #both requisition id and result have changed
                    new_record.record_change = 'both'
                    new_record.old_value = old_record.requisition_id + ":" + old_record.result


    new_record.save()
    return True

def accept_log (log, payload):
    """parse and save a single log message; if does not validate, save the raw data;
    return whether the record validated"""

    logentry = labresults.LabLog(payload=payload)
    logfields = {
        'timestamp': dictval(log, 'at', json_timestamp),
        'message': dictval(log, 'msg'),
        'level': dictval(log, 'lvl'),
        'line': dictval(log, 'ln'),
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
        exclude = ['notification_status','record_change','old_value',
                   'requisition_id_search']

log_rotation_threshold = 5000
def log_viewer (request, daysback='7', source_filter=''):
    try:
        daysback = int(daysback)
    except ValueError:
        #todo: return error - parameter is not an int
        pass

    if daysback <= 0 or daysback >= 10000:
        #todo: return error - parameter out of range
        pass

    #get log records to display - any log entry in a payload that was received in the past N days
    cutoff_date = (datetime.now() - timedelta(days=daysback))
    payloads = labresults.Payload.objects.filter(incoming_date__gte=cutoff_date)
    logs = labresults.LabLog.objects.filter(payload__in=payloads)

    #extract displayable info from log records, remove duplicate (re-sent) entries
    log_info = {}
    meta_logs = [] #meta logs are log messages related to logging itself; they have no line numbers or timestamps
    for log_record in logs:
        if log_record.message == None:
            #skip log entries that weren't parseable
            continue

        if not log_record.payload.source.startswith(source_filter):
            continue

        log_entry = {
            'line': log_record.line,
            'timestamp': log_record.timestamp,
            'level': log_record.level,
            'message': log_record.message,
            'received_on': log_record.payload.incoming_date,
            'received_from': log_record.payload.source,
            'version': log_record.payload.version,
        }
        log_uid = (log_entry['line'], log_entry['timestamp'])

        if log_entry['line'] == -1:
            meta_logs.append(log_entry)
        elif log_uid in log_info:
            if log_entry['received_on'] < log_info[log_uid]['received_on']:
                #save the earliest 'received on' date for re-sent entries
                log_info[log_uid] = log_entry
        else:
            log_info[log_uid] = log_entry
    log_entries = log_info.values()
    log_entries.extend(meta_logs)

    #sort records into chronological order (best-faith effort)
    lines = set(lg['line'] for lg in log_entries)
    #if log entry buffer contains both high- and low-numbered lines, log file rotation may have occurred recently
    wraparound = len(lines | set(range(0, 500))) > 0 and (max(lines) if lines else 0) >= log_rotation_threshold
    #if multiple log messages have the same line #, could suggest the log file was recently erased
    collisions = any(len([lg for lg in log_entries if lg['line'] == ln]) > 1 for ln in lines if ln != -1)
    log_entries.sort(cmp=lambda x, y: log_cmp(x, y, wraparound))

    #format information for display
    log_display_items = []
    for le in log_entries:
        ldi = {
            'type': 'log',
            'line': le['line'],
            'timestamp': '%s.%03d' % (le['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), le['timestamp'].microsecond / 1000),
            'level': level_abbr(le['level']),
            'message': le['message'],
            'received_on': le['received_on'],
            'received_from': recvd_from(le['received_from'], le['version'])
        }

        if ldi['line'] == -1:
            ldi['type'] = 'meta-log'
        elif len(log_display_items) > 0:
            prev_line = log_display_items[-1]['line']
            if prev_line != -1:
                expected_next_line = prev_line + len(log_display_items[-1]['message'].split('\n'))
                cur_line = le['line']

                if cur_line > expected_next_line:
                    log_display_items.append({'type': 'alert', 'message': 'missing log entries (%d lines)' % (cur_line - expected_next_line)})
                elif cur_line < expected_next_line:
                    log_display_items.append({'type': 'alert', 'message': 'logfile rotation (?)'})

        log_display_items.append(ldi)

    return render_to_response('labresults/logview.html',
                              {'display_info': log_display_items, 'collisions': collisions,
                               'days': daysback, 'source': source_filter},
                               context_instance=RequestContext(request))


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

def recvd_from (source, version):
    deployments = {
        'ndola/arthur-davison': 'adch',
        'lusaka/kalingalinga': 'kaling',
        'lusaka/uth': 'uth',
    }

    if source in deployments:
        source_tag = deployments[source]
    elif len(source) <= 10:
        source_tag = source
    else:
        source_tag = source[:5] + '...' + source[-3:]

    return '%s/v%s' % (source_tag, version)

def level_abbr (level):
    return level[0] if level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] else level

def text_date(text):
    delimiters = ('-','/')
    for delim in delimiters:
        text = text.replace(delim,' ')
    a,b,c = text.split()
    if len(a) == 4:
        return date(int(a), int(b), int(c))
    else:
        return date(int(c), int(b), int(a))

@require_GET
def mwana_reports (request):
#    , startdate=datetime.today().date()-timedelta(days=30),
#                    enddate=datetime.today().date(
    from mwana.apps.reports.webreports.reportcreator import Results160Reports
   
    today = datetime.today().date()
    try:
        startdate1 = text_date(request.REQUEST['startdate'])
    except (KeyError, ValueError, IndexError):
        startdate1 = today -timedelta(days=30)

    try:
        enddate1 = text_date(request.REQUEST['enddate'])
    except (KeyError, ValueError, IndexError):
        enddate1 = datetime.today().date()
    startdate = min(startdate1, enddate1, datetime.today().date())
    enddate = min(max(enddate1, startdate1), datetime.today().date())
    
    r = Results160Reports()
    res = r.dbs_sent_results_report(startdate, enddate)

    min_processing_time, max_processing_time, num_of_dbs_processed, \
    num_facs_processing, processing_time =\
    r.dbs_avg_processing_time_report(startdate, enddate)

    min_entering_time, max_entering_time, num_of_rsts_entered, \
    num_facs_entering, entering_time =\
    r.dbs_avg_entering_time_report(startdate, enddate)

    min_retrieval_time, max_retrieval_time, num_of_dbs_retrieved, \
    num_facs_retrieving, retrieval_time =\
    r.dbs_avg_retrieval_time_report(startdate, enddate)

    min_turnaround_time, max_turnaround_time, num_of_rsts, num_of_facilities,\
    turnaround_time = r.dbs_avg_turnaround_time_report(startdate, enddate)

    min_transport_time, max_transport_time, num_of_dbs, num_of_facs,\
    transport_time = r.dbs_avg_transport_time_report(startdate, enddate)

    samples_reported = r.dbs_sample_notifications_report(startdate, enddate)

    samples_at_lab = r.dbs_samples_at_lab_report(startdate, enddate)

    pending = r.dbs_pending_results_report(startdate, enddate)

    payloads = r.dbs_payloads_report(startdate, enddate)

    births = r.reminders_patient_events_report(startdate, enddate)

    single_bar_length, tt_in_graph, graph = r.dbs_graph_data(startdate, enddate)

    percent_positive_country, percent_negative_country, percent_rejected_country\
                , percent_positive_provinces, percent_negative_provinces\
                , percent_rejected_provinces, total_dbs, months_reporting,\
                days_reporting, year_reporting =r.dbs_positivity_data()

    return render_to_response('labresults/reports.html',
                                {'startdate':startdate,
                                'enddate':enddate,
                                'today':today,
                                'sent_results_rpt':res,
                                'turnaround_time_rpt':turnaround_time,
                                'min_turnaround_time':min_turnaround_time,
                                'max_turnaround_time':max_turnaround_time,
                                'num_of_results':num_of_rsts,
                                'num_of_facilities':num_of_facilities,
                                'processing_time_rpt':processing_time,
                                'min_processing_time':min_processing_time,
                                'max_processing_time':max_processing_time,
                                'num_of_dbs_processed':num_of_dbs_processed,
                                'num_facs_processing':num_facs_processing,
                                'retrieval_time_rpt':retrieval_time,
                                'min_retrieving_time':min_retrieval_time,
                                'max_retrieving_time':max_retrieval_time,
                                'num_of_dbs_retrieved':num_of_dbs_retrieved,
                                'num_facs_retrieving':num_facs_retrieving,
                                'entering_time_rpt':entering_time,
                                'min_entering_time':min_entering_time,
                                'max_entering_time':max_entering_time,
                                'num_of_rsts_entered':num_of_rsts_entered,
                                'num_facs_entering':num_facs_entering,
                                'transport_time_rpt':transport_time,
                                'min_transport_time':min_transport_time,
                                'max_transport_time':max_transport_time,
                                'num_of_dbs':num_of_dbs,
                                'num_of_facs':num_of_facs,
                                'samples_reported_rpt':samples_reported,
                                'samples_at_lab_rpt':samples_at_lab,
                                'pending_results':pending,
                                'payloads_rpt':payloads,
                                'births_rpt':births,
                                'formattedtoday':today.strftime("%d %b %Y"),
                                'formattedtime':datetime.today().strftime("%I:%M %p"),
                                'graph':graph,
                                'single_bar_length':single_bar_length,
                                'tt_in_graph':tt_in_graph,
                                'percent_positive_country':percent_positive_country,
                                'percent_negative_country':percent_negative_country,
                                'percent_rejected_country':percent_rejected_country,
                                'percent_positive_provinces':percent_positive_provinces,
                                'percent_negative_provinces':percent_negative_provinces,
                                'percent_rejected_provinces':percent_rejected_provinces,
                                'total_dbs':total_dbs,
                                'months_reporting':months_reporting,
                                'days_reporting':days_reporting,
                                'year_reporting':year_reporting,
                                },
                                context_instance=RequestContext(request))
