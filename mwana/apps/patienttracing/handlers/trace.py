from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler


class TraceHandler(KeywordHandler):
    '''
    User sends: 
    TRACE MARY
    
    Where mary is patient's name.  Message goes out to all CBAs asking them to find and talk to mary.  
    It also asks them to reply with a message: 
    TOLD MARY
    
    Once they have spoken to the patient and asked them to go to the clinic.
    After a set period of time a follow up message will go out of from the system to the CBA that replied
    asking them to follow up with mary and confirm that she did indeed go to the clinic.
    This is done by having the CBA send the following message to the system:
    CONFIRM MARY
    '''
    pass
