# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.act.models import VerifiedNumber
from mwana.apps.act.models import Appointment
import json
from datetime import datetime, timedelta
import logging

from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.forms import ModelForm
from django.db import transaction

from mwana.apps.act.models import CHW
from mwana.apps.act.models import Client
from mwana.apps.act.models import Payload
from mwana.apps.act.models import SystemUser
from mwana.decorators import has_perm_or_basicauth
from mwana.apps.locations.models import Location


logger = logging.getLogger('mwana.apps.act.views')


def json_datetime(val):
    """convert a datetime value from the json into a python datetime"""
    try:
        return datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
    except:
        return None


def json_date(val):
    """convert a date value from the json into a python date"""
    try:
        return datetime.strptime(val, '%Y-%m-%d').date()
    except:
        return None


def json_timestamp(val):
    """convert a timestamp value (with milliseconds) from the json into a python datetime"""
    if val[-4] not in ('.', ','):
        return None

    try:
        dt = datetime.strptime(val[:-4], '%Y-%m-%d %H:%M:%S')
        return dt + timedelta(microseconds=1000 * int(val[-3:]))
    except:
        return None


def dictval(dict, field, trans=lambda x: x, trans_none=False, default_val=None):
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
@has_perm_or_basicauth('act.add_payload', 'Act')
@transaction.commit_on_success
def accept_appointments(request):
    """accept data submissions via POST."""

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
    payload = Payload.objects.create(incoming_date=payload_date,
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
    appointments in the database.
    """
    logger.debug('in appointments process_payload')
    if data is None:
        data = json.loads(payload.raw)
    pre_record_creation = transaction.savepoint()
    #parse/save the individual result and logs entries; aggregate whether all succeeded, or if any
    #record failed to validate
    records_validate = True
    if 'client' in data and hasattr(data['client'], '__iter__'):        
        if not accept_client_record(data['client'], payload):
            logger.debug('Client record %s did not validate' % data['client'])
            records_validate = False
    elif 'chw' in data and hasattr(data['chw'], '__iter__'):
        if not accept_chw_record(data['chw'], payload):
            logger.debug('CHW record %s did not validate' % data['chw'])
            records_validate = False    
    elif 'appointment' in data and hasattr(data['appointment'], '__iter__'):
        if not accept_appointment_record(data['appointment'], payload):
            logger.debug('Appointment record %s did not validate' % data['appointment'])
            records_validate = False
    elif 'user' in data and hasattr(data['user'], '__iter__'):
        if not accept_user_record(data['user'], payload):
            logger.debug('User record %s did not validate' % data['user'])
            records_validate = False
    else:
        records_validate = False

    logs_validate = True  # TODO: process logs
    if not (records_validate and logs_validate):
        transaction.savepoint_rollback(pre_record_creation)

    meta_fields = {
        'version': dictval(data, 'version'),
        'source': dictval(data, 'source'),
        'client_timestamp': dictval(data, 'now', json_datetime),
        'info': dictval(data, 'info'),
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


def normalize_clinic_id(zpct_id):
    """turn the ZPCT clinic id format into the MoH clinic id format"""
    return zpct_id[:-1] if zpct_id[-1] == '0' and len(zpct_id) == 7 else zpct_id


def map_result(verbose_result):
    return verbose_result


def accept_client_record(record, payload):
    """parse and save an individual record, updating the notification flag if necessary; if record
    does not validate, nothing is saved; existing records are updated as necessary; return whether
    the record validated"""

    #retrieve existing record for id, if it exists
    uuid = dictval(record, 'uuid')
    old_record = None
    if uuid:
        try:
            old_record = Client.objects.get(uuid=uuid)
        except Client.DoesNotExist:
            pass

    def cant_save(message):
        message = 'cannot save record: ' + message
        if old_record:
            message += '; original record [%s] untouched' % uuid
        message += '\nrecord: %s' % str(record)
        logger.error(message)

        #validate required identifying fields

    for req_field in ('uuid', 'nupin', 'location'):
        if dictval(record, req_field) is None:
            cant_save('required field %s missing' % req_field)
            return False

    #validate clinic id
    clinic_code = normalize_clinic_id(str(dictval(record, 'location')))
    try:
        clinic_obj = Location.objects.get(slug=clinic_code)
    except Location.DoesNotExist:
        logger.warning('clinic id %s is not a recognized clinic' % clinic_code)
        clinic_obj = None

    #general field validation
    record_fields = {
        'uuid': uuid,
        'national_id': dictval(record, 'nupin'),
        'payload': payload.id if payload else None,
        'location': clinic_obj.id if clinic_obj else None,
        'clinic_code_unrec': clinic_code if not clinic_obj else None,
        'name': dictval(record, 'name'),
        'alias': dictval(record, 'alias'),
        'dob': dictval(record, 'dob', json_date),
        'sex': dictval(record, 'sex'),
        'address': dictval(record, 'address'),
        'short_address': dictval(record, 'short_address'),
        'can_receive_messages': dictval(record, 'sms_on'),
        'zone': dictval(record, 'zone'),
        'phone': dictval(record, 'phone'),
    }

    #need to keep old record 'pristine' so we can check which fields have changed
    old_record_copy = Client.objects.get(uuid=uuid) if old_record else None
    f_client = ClientForm(record_fields, instance=old_record_copy)
    if f_client.is_valid():
        new_record = f_client.save(commit=False)

        if old_record and new_record.phone != old_record.phone:
            new_record.phone_verified = False
        if new_record.phone and len(new_record.phone) in [10, 13]:
            new_record.phone_verified =  VerifiedNumber.objects.filter(number__endswith=new_record.phone).exists()
        if old_record and old_record.connection and new_record.phone in old_record.connection.identity:
            new_record.connection = old_record.connection
        new_record.save()
    else:
        cant_save('validation errors in record: %s' % str(f_client.errors))
        return False
    return True


def accept_chw_record(record, payload):
    """parse and save an individual record, updating the notification flag if necessary; if record
    does not validate, nothing is saved; existing records are updated as necessary; return whether
    the record validated"""

    #retrieve existing record for id, if it exists
    uuid = dictval(record, 'uuid')
    old_record = None
    if uuid:
        try:
            old_record = CHW.objects.get(uuid=uuid)
        except CHW.DoesNotExist:
            pass

    def cant_save(message):
        message = 'cannot save record: ' + message
        if old_record:
            message += '; original record [%s] untouched' % uuid
        message += '\nrecord: %s' % str(record)
        logger.error(message)

    #validate required identifying fields
    for req_field in ('uuid', 'phone', 'location'):
        if dictval(record, req_field) is None:
            cant_save('required field %s missing' % req_field)
            return False

    #validate clinic id
    clinic_code = normalize_clinic_id(str(dictval(record, 'location')))
    try:
        clinic_obj = Location.objects.get(slug=clinic_code)
    except Location.DoesNotExist:
        logger.warning('clinic id %s is not a recognized clinic' % clinic_code)
        clinic_obj = None

    #general field validation
    record_fields = {
        'uuid': uuid,
        'national_id': dictval(record, 'national_id'),
        'payload': payload.id if payload else None,
        'location': clinic_obj.id if clinic_obj else None,
        'clinic_code_unrec': clinic_code if not clinic_obj else None,
        'name': dictval(record, 'name'),
        'dob': dictval(record, 'dob', json_date),
        'sex': dictval(record, 'sex'),
        'address': "%s. (Zone %s)" % (dictval(record, 'village'), dictval(record, 'zone')),
        'phone': dictval(record, 'phone'),
    }

    #need to keep old record 'pristine' so we can check which fields have changed
    old_record_copy = CHW.objects.get(uuid=uuid) if old_record else None
    f_cha = CHAForm(record_fields, instance=old_record_copy)
    if f_cha.is_valid():
        new_record = f_cha.save(commit=False)

        if old_record and new_record.phone != old_record.phone:
            new_record.phone_verified = False
        if new_record.phone and len(new_record.phone) in [10, 13]:
            new_record.phone_verified =  VerifiedNumber.objects.filter(number__endswith=new_record.phone).exists()
        if old_record and old_record.connection and new_record.phone in old_record.connection.identity:
            new_record.connection = old_record.connection
        new_record.save()
    else:
        cant_save('validation errors in record: %s' % str(f_cha.errors))
        return False
    return True


def accept_appointment_record(record, payload):
    """parse and save an individual record, updating the notification flag if necessary; if record
    does not validate, nothing is saved; existing records are updated as necessary; return whether
    the record validated"""

    #retrieve existing record for id, if it exists
    uuid = dictval(record, 'uuid')
    old_record = None
    if uuid:
        try:
            old_record = Appointment.objects.get(uuid=uuid)
        except Appointment.DoesNotExist:
            pass

    def cant_save(message):
        message = 'cannot save record: ' + message
        if old_record:
            message += '; original record [%s] untouched' % uuid
        message += '\nrecord: %s' % str(record)
        logger.error(message)

    #validate required identifying fields
    for req_field in ('uuid', 'client', 'type', 'date'):
        if dictval(record, req_field) is None:
            cant_save('required field %s missing' % req_field)
            return False

    #validate clinic id
    client_uuid = dictval(record, 'client')
    cha_uuid = dictval(record, 'chw')
    try:
        client_obj = Client.objects.get(uuid=client_uuid)
    except Client.DoesNotExist:
        cant_save('Unrecognized client uuid %s' % client_uuid)
        return False
    try:
        cha_obj = CHW.objects.get(uuid=cha_uuid)
    except CHW.DoesNotExist:
        logger.warning('CHA uuid %s is not a recognized CHA' % cha_uuid)
        cha_obj = None

    #general field validation
    record_fields = {
        'uuid': uuid,
        'national_id': dictval(record, 'national_id'),
        'payload': payload.id if payload else None,
        'client': client_obj.id if client_obj else None,
        'cha_responsible': cha_obj.id if cha_obj else None,
        'date': dictval(record, 'date', json_date),
        'type': dictval(record, 'type').lower(),
    }

    #need to keep old record 'pristine' so we can check which fields have changed
    old_record_copy = Appointment.objects.get(uuid=uuid) if old_record else None
    f_appointment = AppointmentForm(record_fields, instance=old_record_copy)
    if f_appointment.is_valid():
        new_record = f_appointment.save(commit=False)

        # @type new_record Appointment
        if old_record and new_record.status != old_record.status:
            new_record.status = old_record.status
        if old_record and (not new_record.notes) and new_record.notes != old_record.notes:
            new_record.notes = old_record.notes
        new_record.save()
    else:
        cant_save('validation errors in record: %s' % str(f_appointment.errors))
        return False
    return True


def accept_user_record(record, payload):

    name = dictval(record, 'name')
    print "-"* 100
    print name
    print '+'*100
    old_record = None
    if name:
        try:
            old_record = SystemUser.objects.get(name=name)
        except SystemUser.DoesNotExist:
            pass

    def cant_save(message):
        message = 'cannot save record: ' + message
        if old_record:
            message += '; original record [%s] untouched' % name
        message += '\nrecord: %s' % str(record)
        logger.error(message)
        

    #validate required identifying fields
    for req_field in ('name', 'token'):
        if dictval(record, req_field) is None:
            cant_save('required field %s missing' % req_field)
            return False

    #general field validation
    record_fields = {
        'name': name,
        'password_slice': dictval(record, 'token'),
        'site': dictval(record, 'loc'),
        }

    old_record_copy = SystemUser.objects.get(name=name) if old_record else None
    f_user = SystemUserForm(record_fields, instance=old_record_copy)
    if f_user.is_valid():
        f_user.save()        
    else:
        cant_save('validation errors in record: %s' % str(f_user.errors))
        return False
    return True


class PayloadForm(ModelForm):
    class Meta:
        model = Payload
        fields = ['version', 'source', 'client_timestamp', 'info']


class ClientForm(ModelForm):
    class Meta:
        model = Client

#        exclude = []


class CHAForm(ModelForm):
    class Meta:
        model = CHW


class AppointmentForm(ModelForm):
        class Meta:
            model = Appointment
            exclude = ['status']

class SystemUserForm(ModelForm):
    class Meta:
        model = SystemUser


log_rotation_threshold = 5000


def log_cmp(a, b, wraparound):
    def get_line(lg):
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


def level_abbr(level):
    return level[0] if level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] else level

