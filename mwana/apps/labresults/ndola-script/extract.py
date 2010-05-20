import pyodbc
import sqlite3
import config
import logging
import logging.handlers
from datetime import datetime, date, timedelta
from datetime import time as timeofday
import time
import re
import random
import json
import urllib2
from urlparse import urlparse
from threading import Thread
import os
import os.path
import bz2

identity = lambda x: x

db_fields = ['sample_id', 'imported_on', 'resolved_on', 'patient_id', 'facility_code', 'collected_on',
             'received_on', 'processed_on', 'result', 'result_detail', 'birthdate', 'child_age', 
             'health_worker', 'health_worker_title', 'sync_status']

def init_logging ():
  """initialize the logging framework"""
  global log
  log = logging.getLogger('extract')
  log.setLevel(logging.DEBUG)
  handler = logging.handlers.RotatingFileHandler(config.log_path, maxBytes=1048576, backupCount=2)
  formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s")
  handler.setFormatter(formatter)
  log.addHandler(handler)
# uncomment for logging to console, if desired
#  log.addHandler(logging.StreamHandler())
init_logging()

def days_ago (n):
  """return the date n days ago"""
  return date.today() - timedelta(days=n)

def dbconn (db):
  """return a database connected to the production (lab access) or staging (UNICEF sqlite) databases"""
  if db == 'prod':
    return pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s' % config.prod_db_path)
# to use the Easysoft Access ODBC driver from linux:
#    return pyodbc.connect('DRIVER={Easysoft ODBC-ACCESS};MDBFILE=%s' % config.prod_db_path)
  elif db == 'staging':
    return sqlite3.connect(config.staging_db_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
  else:
    raise ValueError('do not recognize database [%s]' % db)

def pkey_fetch (curs, query, args=()):
  """query the primary key column of a table and return the results as a set of ids"""
  curs.execute(query, args)
  return set(rec[0] for rec in curs.fetchall())
    
def init_staging_db (lookback):
  """initialize the staging database"""
  create_staging_db()
  archive_old_samples(lookback)
  log.info('staging db initialized')
    
def create_staging_db ():
  """create the tables in the sqlite db"""
  conn = dbconn('staging')
  curs = conn.cursor()

  curs.execute('''
    create table samples (
      sample_id varchar(10) primary key,  --id assigned to sample in lab
      imported_on date,                   --when sample record was discovered by extract script
      resolved_on date,                   --when result was noticed by extract script
      patient_id varchar(100),            --patient 'identifier' from requisition form
      facility_code int,
      collected_on date,                  --date sample was collected at clinic
      received_on date,                   --date sample was received at/entered into lab system
      processed_on date,                  --date sample was tested in lab
      result varchar(20),                 --result: 'positive', 'negative', 'rejected', 'indeterminate', 'inconsistent'
      result_detail varchar(100),         --e.g., reason rejected
      birthdate date,
      child_age int,                      --in months (may be inconsistent with birthdate)
      health_worker varchar(50),          --name of clinic worker collecting sample
      health_worker_title varchar(50),    --title of clinic worker
      sync_status varchar(10) not null default 'new'  --status of record's sync with rapidsms server: 'new', 'updated',
                                                      --'synced', 'historical'
    )
  ''')
    
  conn.commit()
  curs.close()
  conn.close()

def facilities_where_clause ():
  """ensures that only the clinics specified in the config file are entered into the staging database"""
  if config.clinics:
    return 'Facility in (%s)' % ', '.join(config.clinics)
  else:
    return ''

def archive_old_samples (lookback):
  """pre-populate very old samples in the prod db into staging, so they don't show up in 'new record' queries"""
  conn = dbconn('prod')
  curs = conn.cursor()
  sql = "select %s from tbl_Patient where DateReceived < ?" % config.prod_db_id_column
  facilities = facilities_where_clause()
  if facilities:
    sql += ' AND %s' % facilities
  curs.execute(sql, [days_ago(lookback).strftime('%Y-%m-%d')])
  archive_ids = set(norm_id(rec[0]) for rec in curs.fetchall())
  log.info('archiving %d records' % len(archive_ids))
  curs.close()
  conn.close()
  
  conn = dbconn('staging')
  curs = conn.cursor()
  for id in archive_ids:
    curs.execute("insert into samples (sample_id, sync_status) values (?, 'historical')", [id])
  conn.commit()
  curs.close()
  conn.close()
  
def get_ids (db, col, table, normfunc=identity):
  """return a set of all primary key IDs in the given database"""
  conn = dbconn(db)
  curs = conn.cursor()
  sql = 'select %s from %s' % (col, table)
  facilities = facilities_where_clause()
  if db == 'prod' and facilities:
    # if this is the production database, add a filter to ensure that only
    # results for the proper facilities are entered into the staging database
    sql += ' WHERE %s' % facilities
  curs.execute(sql)
  ids = set(normfunc(rec[0]) for rec in curs.fetchall())
  curs.close()
  conn.close()
  return ids
  
def norm_id (lab_id):
  """convert the lab lab id to a more legible, sortable format"""
  if len(lab_id) != 7:
    log.warning('lab id not in expected format [%s]' % lab_id)
    return lab_id
    
  return lab_id[5:7] + '-' + lab_id[0:5]

def denorm_id (sample_id):
  """reverse the conversion in norm_id"""
  if len(sample_id) != 8 or sample_id[2] != '-':
    log.warning('sample id not in expected format [%s]' % sample_id)
    return sample_id
  # make sure it's a string, not unicode, because the ODBC driver doesn't
  # like unicode
  return str(sample_id[3:8] + sample_id[0:2])

def check_new_records ():
  """poll if any new records have appeared in the production db (since last time it was synced to staging)"""
  prod_ids = get_ids('prod', config.prod_db_id_column, 'tbl_Patient', norm_id)
  rsms_ids = get_ids('staging', 'sample_id', 'samples')
  
  deleted_ids = rsms_ids - prod_ids
  new_ids = prod_ids - rsms_ids

  if len(deleted_ids) > 0:
    log.warning('records deleted from lab database! (%s)' % ', '.join(sorted(list(deleted_ids))))

  return (new_ids, deleted_ids)
  
def tx (val, func=identity, nullval=None):
  """helper function for reading values from database"""
  return func(val) if val != None else nullval

def query_sample (sample_id, conn=None):
  """execute a query to retrieve a single sample row from the production db"""
  one_time_conn = (conn == None)
  if one_time_conn:
    conn = dbconn('prod')
    
  curs = conn.cursor()
  sql = '''
    select %s
    from tbl_Patient
    where %s = ?
''' % (', '.join(config.prod_db_columns), config.prod_db_id_column)
  facilities = facilities_where_clause()
  if facilities:
    sql += ' AND %s' % facilities
  curs.execute(sql, [denorm_id(sample_id)])
    
  results = curs.fetchall()
  curs.close()
  
  if one_time_conn:
    conn.close()
    
  if len(results) == 0:
    raise ValueError('sample [%s] not found' % sample_id)

  return results[0]
    
def read_sample_record (sample_id, conn=None):
  """read and process/clean up a single sample row for the lab db"""
  sample_row = query_sample(sample_id, conn)
  
  sample = {}
  sample['sample_id'] = sample_id
  sample['patient_id'] = sample_row[0]
  sample['facility_code'] = sample_row[1] 
  sample['collected_on'] = tx(sample_row[2], lambda x: x.date())
  sample['received_on'] = tx(sample_row[3], lambda x: x.date())
  sample['processed_on'] = tx(sample_row[4], lambda x: x.date())
  sample['birthdate'] = tx(sample_row[9], lambda x: x.date())
  sample['child_age'] = sample_row[10]
  sample['sex'] = tx(sample_row[11], lambda x: {1: 'm', 2: 'f'}[x])
  sample['mother_age'] = sample_row[12]
  sample['health_worker'] = sample_row[13]
  sample['health_worker_title'] = sample_row[14]

  detected = tx(sample_row[5], lambda x: {1: '+', 2: '-', 3: '?'}[x])
  rejected = tx(sample_row[6], lambda x: x == 1)
  
  if not rejected:
    if detected == '+':
      result = 'positive'
    elif detected == '-':
      result = 'negative'
    elif detected == '?':
      result = 'indeterminate'
    else:
      result = None
  else:
    if detected in ('+', '-'):
      result = 'inconsistent'
    else:
      result = 'rejected'
      
  if result == 'inconsistent':
    result_detail = ('positive' if detected == '+' else 'negative') + '/rejected'
  elif result == 'rejected':
    reject_reason = sample_row[7]
    
    if reject_reason in (1, 2, 3, 4, 5):
      result_detail = {
        1: 'technical problems',
        2: 'improper labelling',
        3: 'insufficient blood',
        4: 'layered/clotted',
        5: 'improper packaging',
      }[reject_reason]
    elif reject_reason == 9:
      reject_reason_other = tx(sample_row[8], nullval='unspecified')
      result_detail = 'other: ' + reject_reason_other
    else:
      result_detail = 'unknown'
  else:
    result_detail = None  
  
  sample['result'] = result
  sample['result_detail'] = result_detail
      
  return sample  

def read_staged_record (sample_id, conn=None):
  """read a saved record from the staging db"""
  one_time_conn = (conn == None)
  if one_time_conn:
    conn = dbconn('staging')
    
  curs = conn.cursor()
  curs.execute('''
    select %s from samples
    where sample_id = '%s'
    ''' % (', '.join(db_fields[1:]), sample_id))
    
  results = curs.fetchall()
  curs.close()  
  if one_time_conn:
    conn.close()

  if len(results) == 0:
    raise ValueError('sample [%s] not found' % sample_id)

  sample_row = results[0]
  
  sample = {}
  for i in range(0, len(db_fields)):
    sample[db_fields[i]] = sample_row[i - 1] if i >= 1 else sample_id

  return sample
  
def get_update_ids (deleted_ids):
  """get the ids of sample records that still lie within the various 'update listening' windows"""
  conn = dbconn('staging')
  curs = conn.cursor()

  def sample_window(curs, result_clause, date_field, window):
    return pkey_fetch(curs, '''
      select sample_id from samples
      where result %s and %s >= ? and sync_status != 'historical'
    ''' % (result_clause, date_field), [days_ago(window)]) - deleted_ids
  
  #ids for records where result reported; still listening for any changes to record
  update_window_ids = sample_window(curs, "in ('positive', 'negative', 'rejected')", 'resolved_on', config.result_window)
  
  #ids for records where status indetermined; waiting for followup/resolution updates
  incomplete_window_ids = sample_window(curs, "in ('indeterminate', 'inconsistent')", 'resolved_on', config.unresolved_window)
  
  #ids for records still awaiting test result 
  testing_window_ids = sample_window(curs, 'is null', 'imported_on', config.testing_window)  

  curs.close()
  conn.close()
  
  return (update_window_ids, incomplete_window_ids, testing_window_ids)
  
def query_prod_records ():
  """get all records of interest from the lab database (new records and records for which still listening for updates)"""
  (new_ids, deleted_ids) = check_new_records()
  (update_window_ids, incomplete_window_ids, testing_window_ids) = get_update_ids(deleted_ids)
  ids_of_interest = new_ids | update_window_ids | incomplete_window_ids | testing_window_ids
  
  log.info('querying records of interest from lab: %d total%s; %d new; %d resolved; %d in limbo; %d untested' %
            (len(ids_of_interest), (' (+ %d to delete)' % len(deleted_ids)) if len(deleted_ids) > 0 else '',
            len(new_ids), len(update_window_ids), len(incomplete_window_ids), len(testing_window_ids)))
  
  records = []
  conn = dbconn('prod')
  for id in ids_of_interest:
    if id in new_ids:
      source = 'new'
    elif id in update_window_ids:
      source = 'update-resolved'
    elif id in incomplete_window_ids:
      source = 'update-incomplete'
    elif id in testing_window_ids:
      source = 'update-untested'
  
    records.append((source, read_sample_record(id, conn)))
  conn.close()

  return (records, deleted_ids)
  
def pull_records ():
  """pull record updates from lab to the staging db"""
  try:
    (records, deleted_ids) = query_prod_records()
  except:
    log.exception('error accessing lab database (read-only); staging database not touched')
    raise RuntimeError('caught')
  
  try:
    conn = dbconn('staging')
    curs = conn.cursor()
    
    for del_id in deleted_ids:
      delete_record(del_id, curs)
    
    newcount = 0
    updatecount = 0
    newcount_filt = 0
    updatecount_filt = 0
    for (source, record) in records:
      (result, filt) = process_record(record, source, curs)
      if result == 'new':
        newcount += 1
        if filt:
          newcount_filt += 1
      elif result == 'update':
        updatecount += 1
        if filt:
          updatecount_filt += 1
      
    conn.commit()
    if config.clinics:
      log.info('staging db: added %d (%d) new records, updated %d (%d) existing records, deleted %d records' %
          (newcount, newcount_filt, updatecount, updatecount_filt, len(deleted_ids)))
    else:
      log.info('staging db: added %d new records, updated %d existing records, deleted %d records' % (newcount, updatecount, len(deleted_ids)))
  except:
    log.exception('error syncing data to staging database; attemping to rollback')
    conn.rollback()
    raise RuntimeError('caught')
  finally:
    curs.close()
    conn.close()
  
def process_record (record, source, curs):
  """process a single record of interest an mirror data to the staging db"""
  filt = record['facility_code'] in config.clinics if config.clinics else True
  
  if source == 'new':
    record['imported_on'] = date.today()
    record['sync_status'] = 'new'
    record['resolved_on'] = date.today() if record['result'] != None else None
    add_record(record, curs)
    return ('new', filt)
    
  else: #existing record
    #check if any fields changed
    existing_record = read_staged_record(record['sample_id'])
    changed_fields = []
    for k, v in record.items():
      if k in existing_record and v != existing_record[k]:
        changed_fields.append(f)
    
    #if the record has changed
    if len(changed_fields) > 0:
      log.info('record [%s] updated: %s' % (record['sample_id'], ', '.join(sorted(list(changed_fields)))))
    
      record['sync_status'] = 'update'
      #fill in staging-only fields
      for f in ('imported_on', 'resolved_on'):
        record[f] = existing_record[f]
      
      #if 'result' changed from a non-definitive result to a definitive result, reset the 'resolved_on' counter
      if 'result' in changed_fields and update_resolved_date(existing_record['result'], record['result']):
        record['resolved_on'] = date.today()
        
      update_record(record, curs)
      return ('update', filt)
    else:
      return (None, None)

def update_resolved_date (old_result, new_result):
  """whether to reset the 'resolved on' counter based on change in result status"""
  if old_result == None: #new result must be different, therefore not None
    return True
  elif old_result in ('indeterminate', 'inconsistent') and new_result in ('positive', 'negative', 'rejected'):
    return True
  else:
    return False
      
def add_record (record, curs):
  """insert a new sample record into staging"""
  curs.execute('''
    insert into samples (%s) values (%s)
  ''' % (', '.join(db_fields), ', '.join(['?' for f in db_fields])), [record[f] for f in db_fields])
   
def update_record (record, curs):
  """update a record in staging; delete then re-add, because the sql is easier"""
  delete_record(record['sample_id'], curs)
  add_record(record, curs)

def delete_record (sample_id, curs):
  curs.execute('delete from samples where sample_id = ?', [sample_id])      
  

def parse_log_line (logln, lnum=-1):
  """parse the text line of a single log entry"""
  logentry = {}
  pieces = logln.split(';')
  logentry['at'] = pieces[0]
  logentry['lvl'] = pieces[1]
  logentry['msg'] = ';'.join(pieces[2:])
  logentry['ln'] = lnum
  return logentry
  
def read_log_lines ():
  """generator that returns raw lines from the log files in reverse order"""
  for f in [config.log_path, config.log_path + '.1']:
    try:
      lines = [l.rstrip() for l in open(f).readlines() if l.strip()]
    except IOError:
      lines = []
      
    for line in reversed(list(enumerate(lines))):
      yield line

def read_logs ():
  """generator that returns log entries in reverse-chronological order"""
  logline = ''
  for (lnum, line) in read_log_lines():
    if logline == '':
      logline = line
    else:
      logline = line + '\n' + logline
    
    #the first line of a multi-line log entry begins with a datestamp
    if re.match('[0-9]{4}-[0-9]{2}-[0-9]{2}', logline):
      yield parse_log_line(logline, lnum)
      logline = ''
    
  if logline != '':
    yield parse_log_line('2000-01-01 00:00:00,000;WARNING;incomplete log entry:[%s]' % logline)
      
def get_unsynced_logs ():
  """return a list of all log entries that have not been synced to the server"""
  sync_msg = 'sync successful'
  coll_msg = 'logs collected'
  reached_sync_point = False
  reached_coll_point = False
  
  logs = []
  for logentry in read_logs():
    if logentry['msg'] == coll_msg:
      if reached_sync_point:
        reached_coll_point = True
        break
    else:
      if logentry['msg'] == sync_msg:
        reached_sync_point = True
    
      logs.append(logentry)
  if not reached_coll_point:
    logs.append(parse_log_line('2000-01-01 00:00:00,000;WARNING;reached end of logs'))

  return logs
  
def get_unsynced_records ():
  """return the set of records that need to be synced to rapidsms"""
  conn = dbconn('staging')
  curs = conn.cursor()
  unsynced_ids = pkey_fetch(curs, "select sample_id from samples where sync_status in ('new', 'update')")
  curs.close()
  
  records = []
  for id in unsynced_ids:
    records.append(read_staged_record(id, conn))
  conn.close()
  
  return records
  
def retry_task (task, retry_sched):
  """execute a task, retrying the task a fixed number of times until success
  
  the task is encapsulated in the 'task' object; see the *Task classes. the max number of retries
  and delays between them is determined by the retry_sched param, a list of retry_delays in seconds"""
  success = False
  tries = 0
  total_tries = len(retry_sched) + 1

  while not success and tries < total_tries:
    success = task.do()
    tries += 1
    
    if not success:
      if tries < total_tries:
        retry_wait = retry_sched[tries - 1]
        task.hook_fail_retry(tries, total_tries, retry_wait)
        time.sleep(retry_wait)
      else:
        task.hook_fail(total_tries)
    else:
      task.hook_success(tries, total_tries)

  return (success, task.result(success))

"""
class Task:
  def do:
      execute the task at hand; return True if successful, False if not; NEVER throw an exception

  def hook_success (tries, total_tries):
      called if task is successful; tries is the attempt # that succeeded, total_tries the max # of
      attempts that would have been allowed

  def hook_fail (total_tries):
      called if the task is unsuccessful after exhausting all attempts
      
  def hook_fail_retry (tries, total_tries, retry_wait):
      called if the taks is unsuccessful on a given attempt, and another run will be attempted; tries
      is the attempt # that just failed, retry_wait is the delay in second before the next attempt
      
  def result (success):
      return the result of the task; success is whether execution was successful (note: this result will
      usually have to be cached in a class variable in do()
"""

class DBSyncTask:
  """retryable task for syncing the lab and staging databases"""
  
  def do (self):
    try:
      pull_records()
      return True
    except RuntimeError:
      return False
    except:
      log.exception('unexpected error while syncing db')
      return False

  def hook_success (self, tries, total_tries):
    log.info('db sync successful on attempt %d' % tries)

  def hook_fail (self, total_tries):
    log.info('all db sync attempts failed')
  
  def hook_fail_retry (self, tries, total_tries, retry_wait):
    log.info('db sync attempt %d of %d failed; trying again in %d minutes' % (tries, total_tries, retry_wait / 60))
      
  def result (self, success):
    return None
      
class GetUnsyncedRecordsTask:
  """retryable task for pulling the set of records to sync from the staging database"""

  def do (self):
    try:
      self.records = get_unsynced_records()
      return True
    except:
      log.exception('could not read records to sync from staging database')
      return False

  def hook_success (self, tries, total_tries):
    if tries > 1:
      log.info('successfully read records to sync on attempt %d' % tries)
  
  def hook_fail (self, total_tries):
    log.info('could not read records to sync; no records will be sent in this payload')
  
  def hook_fail_retry (self, tries, total_tries, retry_wait):
    pass
    
  def result (self, success):
    return self.records if success else []
  
def sync_databases ():
  """sync the lab and staging databases"""
  retry_task(DBSyncTask(), [60*x for x in config.db_access_retries])

def condense_record (record):
  """trim unnecessary fields and shorten field names to condense sample record size for transmission"""

  def replace_field (rec, old, new):
    rec[new] = rec[old]
    del rec[old]

  del record['imported_on']
  del record['resolved_on']
  replace_field(record, 'sample_id', 'id')
  replace_field(record, 'patient_id', 'pat_id')
  replace_field(record, 'facility_code', 'fac')
  replace_field(record, 'collected_on', 'coll_on')
  replace_field(record, 'received_on', 'recv_on')
  replace_field(record, 'processed_on', 'proc_on')
  replace_field(record, 'health_worker', 'hw')
  replace_field(record, 'health_worker_title', 'hw_tit')
  replace_field(record, 'sync_status', 'sync')
  replace_field(record, 'birthdate', 'dob')
 
  return record
  
def aggregate_submit_data():
  """collect all the different types of data to be sent to rapidsms (sample records, log entries),
  and return as a unified list of datums"""

  #get sample records
  sync_records = retry_task(GetUnsyncedRecordsTask(), [30, 60, 120])[1]
  sync_records = [condense_record(rec) for rec in sync_records]
  
  #get logs
  try:
    logs = get_unsynced_logs()
    log.info('logs collected')
  except:
    log.exception('could not extract logs for submission')
    logs = []

  log.info('%d sample records and %d log entries to send' % (len(sync_records), len(logs)))
  return interlace_data(sync_records, logs)
  
def interlace_data (records, logs):
  """we attempt to chunk the data into many small submissions to help mitigate the effect of flaky connections;
  this function attempts to optimize the distribution of our data records in case only a few POSTs get through"""
  
  #send logs first in reverse-chron order (logs are passed in already sorted)
  for log in logs:
    yield ('log', log)
    
  #then send records in random order
  random.shuffle(records)
  for rec in records:
    yield ('rec', rec)
  
class JSONEncoderWithDate(json.JSONEncoder):
  """extension to base json encoder that supports dates"""
  def __init__(self):
    json.JSONEncoder.__init__(self, ensure_ascii=False)
    
  def default (self, o):
    if isinstance(o, datetime):
      return o.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(o, date):
      return o.strftime('%Y-%m-%d')
    else:
      return json.JSONEncoder.default(self, o)
  
def to_json (data):
  """convert object to json"""
  return JSONEncoderWithDate().encode(data)
  
def chunk_submissions (data_stream):
  """turn the stream of data objects into transmission chunks of (approximate) max size"""
  chunk_size_limit = config.transport_chunk / (config.compression_factor if config.send_compressed else 1.)
  
  chunk, size = [], 0
  for datum in data_stream:
    (type, data) = datum
    chunk.append(datum)
    size += len(to_json(data))
    
    if size >= chunk_size_limit:
      yield chunk
      chunk, size = [], 0
  
  if len(chunk) > 0:
    yield chunk

class Payload:
  """a container class that represents a json payload and the sample ids of the records contained within it"""
  def __init__ (self, chunk=[], id='.'):
    self.json, self.record_ids = self.create_payload(chunk, id)
    
  def create_payload (self, chunk, id):
    types = {'rec': [], 'log': []}
    record_ids = []
    
    for datum in chunk:
      (type, data) = datum
      types[type].append(data)
      if type == 'rec':
        record_ids.append(data['id'])
        
    json_struct = {}
    json_struct['source'] = config.source_tag
    json_struct['version'] = config.version
    json_struct['now'] = datetime.now()
    json_struct['info'] = id
    json_struct['samples'] = types['rec']
    json_struct['logs'] = types['log']
    json = to_json(json_struct)
    
    if config.send_compressed:
      json = bz2.compress(json)
    
    return (json, record_ids)

def connection (payload):
  """undertake the actual http(s) connection; report success or failure with message"""
  try:
    authinfo = urllib2.HTTPBasicAuthHandler()
    urlinfo = urlparse(config.submit_url)
    authinfo.add_password(uri=urlinfo[0] + '://' + urlinfo[1], **config.auth_params)
    opener = urllib2.build_opener(authinfo)
    urllib2.install_opener(opener)

    headers = {'Content-Type': 'text/json'}
    if config.send_compressed:
      headers['Content-Transfer-Encoding'] = 'bzip2'
    
    try:
      f = urllib2.urlopen(urllib2.Request(config.submit_url, payload.json, headers=headers))
      response = f.read()
      code = f.code
      
      if response == 'SUCCESS' and code == 200:
        return (True, None)
      else:
        return (False, 'http response> %d: %s' % (code, response))
    except urllib2.HTTPError, e:
      return (False, 'http response> %d' % e.code)
  except Exception, e:
    return (False, '%s: %s' % (type(e), str(e)))
    
class UpdateSyncFlagTask:
  """retryable task to update the 'sync' flag of records that were successfully sent"""

  def __init__ (self, payload):
    self.payload = payload

  def do (self):
    try:
      try:
        conn = dbconn('staging')
        curs = conn.cursor()
        for id in self.payload.record_ids:
          curs.execute("update samples set sync_status = 'synced' where sample_id = ?", [id])
        conn.commit()        
        return True
      except:
        log.exception('unable to update sync flag in records')
        conn.rollback()
        return False
      finally:
        curs.close()
        conn.close()
    except: #can we say 'paranoia'?
      log.exception('unexpected error when updating sync flag')
      return False

  def hook_success (self, tries, total_tries):
    if tries > 1:
      log.info('successfully updated sync flag on attempt %d' % tries)
    
  def hook_fail (self, total_tries):
    log.warning('successfully sent records, but failed to update sync flag; records will be resent in next batch')  
  
  def hook_fail_retry (self, tries, total_tries, retry_wait):
    pass
    
  def result (self, success):
    return None
  
def update_sync_flag (payload):
  """update the sync flag of successfully sent records"""
  retry_task(UpdateSyncFlagTask(payload), [30, 30])
  
def trunc (text):
  """error message can come from arbitrary http response, so check that length is reasonable"""
  limit = 300
  return text if len(text) < limit else (text[:limit-10] + '...truncated')
  
def send_payload (payload):
  """send an individual payload and update the database to reflect success"""
  (success, fail_reason) = connection(payload)

  if success:
    update_sync_flag(payload) #even if this fails, we don't want to count it as a 'send' failure, so we still return success = True
  else:
    log.warning('failed send attempt: ' + trunc(fail_reason))
  return success
    
class SendAllTask:
  """task manager for sending N payloads, allowing a certain number of retries"""
  def __init__ (self, payloads):
    self.payloads = payloads
    self.i = 0
  
  def do (self):
    while self.i < len(self.payloads):
      success = send_payload(self.payloads[self.i])
      if success:
        self.i += 1
        print 'sent payload %d of %d' % (self.i, len(self.payloads))
      else:
        return False
    return True
    
  def hook_success (self, tries, total_tries):
    log.info('sync successful')
    
  def hook_fail (self, total_tries):
    log.warning('too many failed send attempts; aborting send; %d of %d payloads successfully transmitted' % (self.i, len(self.payloads)))
    
  def hook_fail_retry (self, tries, total_tries, retry_wait):
    log.warning('failed send on payload %d of %d; %d tries left; resuming in %d seconds' % (self.i + 1, len(self.payloads), total_tries - tries, retry_wait))
    
  def result (self, success):
    return None
    
def run_rasdial (args):
  output = os.popen('rasdial ' + args).read()
  output = ' // '.join(output.strip().split('\n'))
  if output.find('Command completed successfully') == -1:
    log.warning('enabling/disabling network may have failed: ' + output)
    
def enable_network ():
  run_rasdial('Internet /phone:*99***1#')
  time.sleep(10)

def disable_network ():
  run_rasdial('Internet /disconnect')

def transport_payloads (payloads):
  """send all payloads, start to finish"""
  
  if not config.always_on_connection:
    enable_network()
  
  retry_task(SendAllTask(payloads), config.send_retries)
  
  if not config.always_on_connection:
    disable_network()
  
def send_data ():
  """send data to rapidsms"""
  data_stream = aggregate_submit_data()
  chunks = list(chunk_submissions(data_stream))
  
  payloads = [Payload(chunk=chunk, id='%d/%d' % (i + 1, len(chunks))) for (i, chunk) in enumerate(chunks)]
  if len(payloads) == 0: #nb: should rarely, if ever, happen; there will always be a few new log messages
    payloads = [Payload()]
    log.info('no data to send; sending ping message only')
  else:
    log.info('%d payloads to send (%d bytes%s)' % (len(payloads), sum(len(p.json) for p in payloads),
                  ', compressed' if config.send_compressed else ''))
  
  transport_payloads(payloads)
  
def init ():
  """ENTRY POINT: initialze the system"""
  try:
    init_staging_db(config.init_lookback)
  except:
    log.exception('error initializing app')
    raise
  
def main ():
  """ENTRY POINT: run the extract/sync task"""
  log.info('beginning extract/sync task')

  try:
    sync_databases()
    send_data()
  except:
    log.exception('unexpected top-level exception in sync task')
    raise
    
  log.info('extract/sync task complete')
  

  
class SingletonTask:
  """wrapper class to ensure that a function/task has only one executing instance at any given time;
  accomplishes this in a somewhat ghetto manner by polling a shared lockfile"""
  def __init__(self, task, lockfile, poll_freq=20, max_runtime=None, name=''):
    self.task = task
    self.lockfile = lockfile
    self.poll_freq = poll_freq
    self.max_runtime = max_runtime
    self.name = '%s:%04x' % (name, random.randint(0, 2**16 - 1))
    
  def start (self):
    if self.acquire_lock():
      thr = Thread(target=self.task)
      runtime = 0
      
      thr.start()
      while thr.is_alive():
        if self.max_runtime != None and runtime > self.max_runtime:
          log.warning(('task [%s] exceeded its max allowed runtime of %ds; runlock is being released; ' +
              'assume task is hung/stalled, but may still be running!') % (self.name, self.max_runtime))
          break
      
        time.sleep(self.poll_freq)
        runtime += self.poll_freq
        self.refresh_lock()
    
      self.clear_lock()
    else:
      log.info('unable to acquire lock for task [%s]; not running...' % self.name)
    
  def acquire_lock (self):
    lock_stat = self.read_lockfile()
    if lock_stat:
      have_lock = self.monitor_lockfile(lock_stat)
    else:
      have_lock = True
      
    if have_lock:
      self.refresh_lock()
    return have_lock
    
  def read_lockfile (self):
    try:
      if os.path.exists(self.lockfile):
        contents = open(self.lockfile).read()
        if re.match('[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}', contents):
          return contents[:19]
        else:
          return None
      else:
        return None
    except:
      log.exception('could not read lockfile [%s - %s]; proceeding as if unlocked...' % (self.name, self.lockfile))
      return None
  
  def refresh_lock (self):
    try:
      f = open(self.lockfile, 'w')
      f.write('%s\n' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
      f.close()
    except:
      log.exception('cannot update lockfile [%s - %s]; singleton guarantees no longer valid, but not much we can do; proceeding...' % (self.name, self.lockfile))

  def monitor_lockfile (self, val):
    for i in range(0, 6):
      time.sleep(self.poll_freq)
      new_val = self.read_lockfile()
      if new_val != None and val != new_val:
        return False
    log.info('existing lockfile [%s - %s] appears to be from a defunct process; proceeding as if unlocked...' % (self.name, self.lockfile))
    return True
  
  def clear_lock (self):
    try:
      os.remove(self.lockfile)
    except:
      log.exception('could not clear lockfile [%s - %s]; task is now defunct' % (self.name, self.lockfile))
    
def fdelta (delta):
  """convert a timedelta into seconds"""
  return 86400*delta.days + delta.seconds + 1.0e-6*delta.microseconds
    
def fire_task ():
  """launch the extract/sync task"""
  try:
    log.info('launching scheduled task')
    SingletonTask(main, config.task_lock, name='extract/sync', max_runtime=7200).start()
    log.info('task completed')
  except:
    log.exception('top-level exception in firing task!')
    
def is_hit (sched_time, time_a, time_b):
  """return true if the sched_time falls within the bracket times time_a and time_b"""
  if time_a < time_b:
    return time_a <= sched_time and sched_time < time_b
  else: #midnight rollover
    return time_a <= sched_time or sched_time < time_b

def daemon_loop (times, last_ping):
  """core daemon loop that waits for scheduling events and launches the tasks"""
  try:
    log.info('daemon booted; ' + ('previous instance appears to have terminated around %s' % last_ping if last_ping != None
               else 'unknown when previous instance terminated'))

    inst = datetime.now()
    fault_count = 0
    max_faults = 30
  except:
    log.exception('top-level exception in initializing daemon!')

  while True:
    try:
      time.sleep(10)
      new_inst = datetime.now()

      #if new time is before old time, or new time is significantly later than old time, assume
      #system clock changed or something else weird happened; don't fire tasks
      if new_inst < inst or fdelta(new_inst - inst) > 300:
        log.info('time discrepancy detected: ' + ' -> '.join(t.strftime('%Y-%m-%d %H:%M:%S') for t in [inst, new_inst]))
      else:
        time_a = inst.time()
        time_b = new_inst.time()
        sched_hit = any(is_hit(sched_time, time_a, time_b) for sched_time in times)
 
        if sched_hit:
          Thread(target=fire_task).start()    
    
      inst = new_inst
    except:
      log.exception('unhandled exception in core daemon loop!')
      fault_count += 1
      if fault_count == max_faults:
        log.info('too many faults (%d) in daemon loop; shutting down as a precaution...' % max_faults)
        return
  
def parse_sched_params ():
  """parse the scheduling times config parameter"""
  times =[]
  for tstr in config.sched:
    try:
      hour = int(tstr[0:2])
      minute = int(tstr[2:4])
      tm = timeofday(hour, minute)
      times.append(tm)
    except:
      log.exception('can\'t parse time parameter [%s]' % tstr)
  return times
  
def daemon ():
  """ENTRY POINT: background daemon that runs the extract/sync task at scheduled intervals"""
  try:
    log.info('booting daemon... (v%s)' % config.version)
  
    times = parse_sched_params()
    if len(times) == 0:
      log.warning('no scheduled times! nothing to do; exiting...')
      return
    else:
      log.info('scheduled to run at: %s' % ', '.join(t.strftime('%H:%M') for t in sorted(times)))
  
    if config.clinics:
      log.info('filtering by %d clinics: %s' % (len(config.clinics), ', '.join(config.clinics)))
    else:
      log.info('all clinics enabled')
  
    last_ping = SingletonTask(None, config.daemon_lock).read_lockfile()
    SingletonTask(lambda: daemon_loop(times, last_ping), config.daemon_lock, name='daemon').start()
  except:
    log.exception('top-level exception when booting daemon!')
  
if __name__ == "__main__":
  daemon()
