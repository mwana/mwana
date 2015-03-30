# vim: ai ts=4 sts=4 et sw=4
import logging

from datetime import datetime

from django.conf import settings
from django.db.models import Q

from rapidsms.router import send
from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.models import Contact

import mwana.const as const
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.messages import build_printer_results_messages
from mwana.apps.tlcprinters.messages import TLCOutgoingMessage


logger = logging.getLogger(__name__)
REQUEST_CALL_HELP = '''You need to be a registered printer to request
                    bulk printing of results.'''

class RequestCallHandler(KeywordHandler):
    """
    Handles manual request from printer to send verified results or report on
    status.
    """

    keyword = "request"

    def help(self):
        self.respond(REQUEST_CALL_HELP)

    def __identify_printer(self):
        try:
            if self.msg.connections[0].contact is not None:
                printer = None
                contact = self.msg.connections[0].contact
                types = contact.types.values_list()
                for values in types:
                    for i in values:
                        if i == "DBS Printer":
                            printer = contact
                return printer
            else:
                return None
        except ObjectDoesNotExist:
            return None

    def _result_verified(self):
        """
        Only return verified results or those not verified due
        to constraints at the lab.
        """
        return Q(verified__isnull=True) | Q(verified=True)

    def __pending_results(self, clinic):
        """
        Get pending results for the printers.
        """
        if settings.SEND_LIVE_LABRESULTS:
            results = Result.objects.filter(
                clinic=clinic,
                clinic__send_live_results=True)
        return results

    def __verified_pending_results(self, results):
        """
        Returns verified results.
        """
        results = results.filter(notification_status__in=['new', 'notified'])
        return results.filter(self._result_verified())

    def __unprocessed_results(self, results):
        """
        Returns number of unprocessed results.
        """
        results = results.filter(notification_status__in=['unprocessed'])
        return results.count()

    def handle(self):
        printer = self.__identify_printer()
        if printer is None:
            return self.respond(REQUEST_CALL_HELP)

        clinic = printer.clinic if printer.clinic is not None else None
        if clinic is not None:
            pending_results = self.__pending_results(clinic)
            results = self.__verified_pending_results(pending_results)
            unprocessed = self.__unprocessed_results(pending_results)
        if results.count() != 0:
            responses = build_printer_results_messages(results)
            for resp in responses:
                msg = TLCOutgoingMessage([printer.connections[0]], resp)
                msg.send()
            for r in results:
                r.notification_status = 'sent'
                r.result_sent_date = datetime.now()
                r.save()

            contacts = Contact.active.filter(
                Q(location=clinic) | Q(location__parent=clinic),
                Q(types=const.get_clinic_worker_type())).distinct().order_by('pk')
            for contact in contacts:
                msg_notification = (u"Hello {name}, {count} results have sent to "
                       u"the printer at {clinic}.".format(name=contact.name,
                                                          count=results.count(),
                                                          clinic=clinic.name))
                if contact.connections[0] is not None:
                    send(msg_notification, [contact.connections[0]])
        else:
            msg_no_results = "There are no results available for now."
            no_results = TLCOutgoingMessage([printer.connections[0]], msg_no_results)
            no_results.send()
        if unprocessed != 0:
            msg_unprocessed = "%s samples were received and are being"\
                              "processed at the lab." % unprocessed
            pending = TLCOutgoingMessage([printer.connections[0]], msg_unprocessed)
            pending.send()
