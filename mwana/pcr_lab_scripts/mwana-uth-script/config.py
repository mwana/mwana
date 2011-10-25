version = '1.1.0'

sched = ['0930', '1310', '1530']  #scheduling parameters for sync task

# List of clinic ids to send data for; if present, ONLY data for these clinics 
# will accumulate in the staging db and, subsequently, be sent to the MOH 
# server.  If empty or None, data for all clinics will be sent.
clinics = [
  '8080140',
  '8080300',
  '8080150',
  '8080250',
  '8080210',
  '8070990',
  '8070330',
  '8070260',
  '8070350',
  '8070370',
]

#path to the Lab database                                        
import os.path
base_path = os.path.dirname(os.path.abspath(__file__))

staging_db_path = os.path.join(base_path, 'rapidsms_results.db3')
prod_db_path = 'C:\\UTH_PCR\\Data\\UTH_PCR_DATABASE.mdb'
log_path = os.path.join(base_path, 'extract.log')

# the name of the column containing the lab-based ID of the record
prod_db_id_column = 'LabID'

# a list of the column names to select from the lab database, in the following
# order: sample_id, patient_id, facility_code, collected_on, received_on,
# processed_on, result, rejected (boolean), rejection_reason,
# reject_reason_other, birthdate, child_age, child_age_unit, sex, mother_age,
# health_worker, health_worker_title, verified
prod_db_columns = [
  'PatientIDReference',
  'Facility',
  'CollectionDate',
  'DateReceived',
  'HivPcrDate',
  'PcrLabResults',
  'HasSampleBeenRejected',
  'RejectionReasons',
  'RejectionReasonOther',
  'BirthDate',
  'Age',
  'AgeUnit',
  'Sex',
  'MotherAge',
  'RequestingHealthWorker',
  'Designation',
  'ResultsVerified',
]

# adh:
#result_map = {1: '+', 2: '-', 3: '?'}
# uth:
result_map = {
  'Detected': '+',
  'Not detected': '-',
  'Invalid': '?',
  'Sample rejected': 'rejected',
}

#production rapidsms server at MoH
submit_url = 'https://mwana-zambia.unicefinnovation.org/labresults/incoming/'

auth_params = dict(realm='Lab Results', user='uth', passwd='Eedoos9seh')

always_on_connection = False       #if True, assume computer 'just has' internet

result_window = 14     #number of days to listen for further changes after a definitive result has been reported
unresolved_window = 28 #number of days to listen for further changes after a non-definitive result has been
                       #reported (indeterminate, inconsistent)
testing_window = 90    #number of days after a requisition forms has been entered into the system to wait for a
                       #result to be reported

init_lookback = 14     #when initializing the system, how many days back from the date of initialization to report
                       #results for (everything before that is 'archived')
                      
                      
transport_chunk = 5000  #maximum size per POST to rapidsms server (bytes) (approximate)
send_compressed = False  #if True, payloads will be sent bz2-compressed
compression_factor = .2 #estimated compression factor


#wait times if exception during db access (minutes)
db_access_retries = [2, 3, 5, 5, 10]

#wait times if error during http send (seconds)
send_retries = [0, 0, 0, 30, 30, 30, 60, 120, 300, 300]

#source_tag Just a tag for identification
source_tag = 'lusaka/uth'


daemon_lock = base_path + 'daemon.lock'
task_lock = base_path + 'task.lock'
