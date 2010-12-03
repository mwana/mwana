# vim: ai ts=4 sts=4 et sw=4
version = '1.0.3'

sched = ['0930', '1310', '1645']  #scheduling parameters for sync task

# List of clinic ids to send data for; if present, ONLY data for these clinics 
# will accumulate in the staging db and, subsequently, be sent to the MOH 
# server.  If empty or None, data for all clinics will be sent.
clinics = [
  '4020260',
  '4020300',
  '4020230',
  '4030110',
  '4030170',
  '4030290',
  '4030320',
  '4030120',
  '4060130',
  '4060150',
  '4060160',
]

#path to the ZPCT database
prod_db_path = 'C:\\ZPCT_PCR\\Data\\ZPCT_PCR_DATABASE_be.mdb'                                        #ZPCT production DB

base_path = 'C:\\unicef-mwana\\script\\'

staging_db_path = base_path + 'rapidsms_results.db3'
log_path = base_path + 'extract.log'

submit_url = 'https://mwana-zambia.unicefinnovation.org/labresults/incoming/'    #production rapidsms server at MoH

auth_params = dict(realm='Lab Results', user='adh', passwd='aibieV9ree')

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

source_tag = 'ndola/arthur-davison'

daemon_lock = base_path + 'daemon.lock'
task_lock = base_path + 'task.lock'
