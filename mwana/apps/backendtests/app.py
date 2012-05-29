# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.backendtests.models import ForwardedMessage
import logging

import rapidsms
from datetime import datetime
logger = logging.getLogger(__name__)

class App (rapidsms.apps.base.AppBase):
    
    def handle (self, message):
        if message.connection.backend.name != 'zain-smpp':
            return False

        try:
            fm = ForwardedMessage.objects.get(connection=message.connection,
                                            responded=False)
            fm.responded=True
            fm.response = message.text
            fm.date_responded = datetime.now()
            fm.save()
            message.respond("Thank you very much.")
            return True
        except Exception, e:
            logger.warn(e)
            if(message.connection.backend.name=='zain-smpp'):
                return True

    
