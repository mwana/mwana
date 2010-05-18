version = '1.0.3'

sched = ['0930', '1310', '1645']  #scheduling parameters for sync task

#list of clinic ids to send data for; if present, ONLY data for these clinics will be sent
#(though data for all clinics will still accumulate in the staging db); if empty or None,
#data for all clinics will be sent
clinics = None

#path to the ZPCT database
#prod_db_path = 'C:\\ZPCT_PCR\\Data\\ZPCT_PCR_DATABASE_be.mdb'                                        #ZPCT production DB
#prod_db_path = 'C:\\unicef-mwana\\test\\ZPCT_PCR\\Data\\ZPCT_PCR_DATABASE_be.mdb'                    #testing copy of DB -- local copy on lab computer
prod_db_path = 'C:\\Documents and Settings\\Drew Roos\\Desktop\\muana\\db\\ZPCT_PCR_DATABASE_be.mdb' #testing copy of DB -- local machine

#base_path = 'C:\\unicef-mwana\\script\\'
base_path = 'C:\\Documents and Settings\\Drew Roos\\Desktop\\muana\\script\\'

staging_db_path = base_path + 'rapidsms_results.db3'
log_path = base_path + 'extract.log'

#submit_url = 'https://mwana-zambia.unicefinnovation.org/labresults/incoming/'    #production rapidsms server at MoH
submit_url = 'http://127.0.0.1:8000/labresults/incoming/'                        #testing server on local machine

#auth_params = dict(realm='Lab Results', user='adh', passwd='')
auth_params = dict(realm='Lab Results', user='admin', passwd='admin')

always_on_connection = True       #if True, assume computer 'just has' internet

result_window = 14     #number of days to listen for further changes after a definitive result has been reported
unresolved_window = 28 #number of days to listen for further changes after a non-definitive result has been
                       #reported (indeterminate, inconsistent)
testing_window = 90    #number of days after a requisition forms has been entered into the system to wait for a
                       #result to be reported

init_lookback = 14     #when initializing the system, how many days back from the date of initialization to report
                       #results for (everything before that is 'archived')
                      
                      
transport_chunk = 5000  #maximum size per POST to rapidsms server (bytes) (approximate)
send_compressed = True  #if True, payloads will be sent bz2-compressed
compression_factor = .2 #estimated compression factor


#wait times if exception during db access (minutes)
db_access_retries = [2, 3, 5, 5, 10]

#wait times if error during http send (seconds)
send_retries = [0, 0, 0, 30, 30, 30, 60, 120, 300, 300]

#source_tag = 'ndola/arthur-davison'
source_tag = 'ndola/arthur-davison [TEST]'


daemon_lock = base_path + 'daemon.lock'
task_lock = base_path + 'task.lock'