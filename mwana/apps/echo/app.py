import time
from rapidsms.conf import settings
from rapidsms.apps.base import AppBase
from rapidsms.backends.base import BackendBase
from rapidsms.messages import IncomingMessage, OutgoingMessage
from rapidsms.models import Connection

class App(AppBase):
    """
    """


#    def _wait_for_message(self, msg):
#        countdown = settings.MESSAGE_TESTER_TIMEOUT
#        interval  = settings.MESSAGE_TESTER_INTERVAL
#
#        while countdown > 0:
#            if msg.processed:
#                break
#
#            # messages are usually processed before the first interval,
#            # but pause a (very) short time before checking again, to
#            # avoid pegging the cpu.
#            countdown -= interval
#            time.sleep(interval)


    def start(self):
        try:
            self.backend

        except KeyError:
            self.info(
                "To use the mwana echo app, you must add a  " +\
                "backend named 'zain' to your INSTALLED_BACKENDS")


    @property
    def backend(self):
        bb = None
        b = self.router.backends
        for i in b:
            bb = b[i]         
        return bb

    def ajax_GET_status(self,get):
        backends = self.router.backends
        status = {}
        for b in backends:
            status[backends[b].name] = backends[b].status()
        return str(status)
    
    def ajax_POST_send_test_message(self, get, post):
        msg = OutgoingMessage(Connection.objects.all()[0], "Heyo! Test Message ftw.")
        msg.send()
        return "Message sent"

    def ajax_GET_available_backends(self, get):
        return str(self.router.backends)

#    def ajax_POST_send(self, get, post):
#        msg = self.backend.receive(
#            post.get("identity", None),
#            post.get("text", ""))
#
#        self._wait_for_message(msg)
#        return True
#
#
#    def ajax_GET_log(self, get):
#        def _direction(msg):
#            if isinstance(msg, OutgoingMessage): return "out"
#            if isinstance(msg, IncomingMessage): return "in"
#            return None
#
#        def _json(msg):
#            return {
#                "identity": msg.connection.identity,
#                "direction": _direction(msg),
#                "text": msg.text }
#
#        return map(_json, self.backend.bucket)
