#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import re
from mwana.apps.labresults.models import Result
from rapidsms.contrib.handlers import KeywordHandler

UNGREGISTERED = "Sorry, you must be registered with Results160 to report DBS \
samples sent. If you think this message is a mistake, respond with keyword 'HELP'"
HELP          = "To request for results for a DBS sample, send RESULT <sampleid>. \
E.g result ID45"
SORRY         = "Sorry, we didn't understand that message."

class ResultsHandler(KeywordHandler):
    """
    clinic_worker >> RESULT <sampleid>
    clinic_worker << <sampleid>: <result>

    Unknown Sample
    clinic_worker << Sorry, I don't know about a sample with id %(requisition_id)s.
    Please check your DBS records and try again.

    No results yet*
    clinic_worker << The results for sample %(requisition_id)s are not yet ready. You will be notified when they are.
    * this may not be possible, depending on the data we are able to collect
    """

    keyword = "result|results|resut|resuts"
    PATTERN = re.compile(r'(\S+)')

    def help(self):
        self.respond(HELP)

    def handle(self, text):
        text = text.strip()

        if not self.msg.contact:
            self.respond(UNGREGISTERED)
            return
        if text == '9999':
            try:
                Result.objects.get(requisition_id =text,
                                            clinic = self.msg.contact.location)                
            except Result.DoesNotExist:
                self.respond("Sample 9999: Detected. Please record these results in your clinic records and"
            " promptly delete them from your phone. Thanks again")
                return

        requisition_ids = self.PATTERN.findall(text)
        #we do not expect this
        if requisition_ids is None:
            self.respond("%s %s" % (SORRY, HELP))
            return
        ready_sample_results = []
        unready_sample_results = []
        unfound_sample_results = []
        for requisition_id in requisition_ids:
            results = Result.objects.order_by('pk').filter(
                                                           requisition_id__iexact
                                                           =requisition_id,
                                                           clinic
                                                           =self.msg.contact.location)
            if results:
                for result in results:
                    if result.result and len(result.result.strip()) > 0:
                        if result.result.upper() in 'PN':
                            ready_sample_results.append(
                                    "%(req_id)s: %(res)s" %
                                    {'req_id':result.requisition_id,
                                    'res':result.get_result_display()})
                            result.notification_status = "sent"
                            result.save()
                        else:
                            unready_sample_results.append(requisition_id)
                    else:
                        unready_sample_results.append(requisition_id)
            else:
                unfound_sample_results.append(requisition_id)
        if ready_sample_results:
            resultsmsg = ". ".join(rst for rst in ready_sample_results)
            self.respond("%s. Please record these results in your clinic records and"
            " promptly delete them from your phone. Thanks again" % resultsmsg)

        if unready_sample_results:
            self.respond("The results for sample(s) %(requisition_id)s are "
                        "not yet ready. You will be notified when they are ready.",
                        requisition_id=', '.join(str(requisition_id) for requisition_id in unready_sample_results))

        if unfound_sample_results:
            if len(unfound_sample_results) == 1:
                self.respond("There are currently no results available for "
                             "%s. Please check if the SampleID is "
                             "correct or sms HELP if you have been waiting "
                             "for 2 months or more" % requisition_id)
            else:
                ids = ', '.join(str(requisition_id)
                                for requisition_id in unfound_sample_results)
                self.respond("There are currently no results available for "
                             "%s. Please check if the SampleID's are "
                             "correct or sms HELP if you have been waiting "
                             "for 2 months or more" % ids)
