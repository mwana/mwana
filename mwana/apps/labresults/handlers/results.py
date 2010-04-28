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
    clinic_worker << Sorry, I don't know about a sample with id %(sample_id)s.
    Please check your DBS records and try again.

    No results yet*
    clinic_worker << The results for sample %(sample_id)s are not yet ready. You will be notified when they are.
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

        sample_ids=self.PATTERN.findall(text)
        #we do nott expect this
        if sample_ids is None:
            self.respond("%s %s" % (SORRY, HELP))
            return
        ready_sample_results = []
        unready_sample_results = []
        unfound_sample_results = []
        for sample_id in sample_ids:
            try:
                results = Result.objects.filter(sample_id__iexact=sample_id, clinic=self.msg.contact.location)
                if results:
                    for result in results:
                        if result.result and len(result.result.strip()) > 0:
                            ready_sample_results.append("%s: %s" % (result.sample_id, result.get_result_display()))
                            result.notification_status = "sent"
                            result.save()
                        else:
                            unready_sample_results.append(sample_id)
                else:
                    unfound_sample_results.append(sample_id)
            except Exception, e:
                self.error(e)
        if ready_sample_results:
            self.respond(", ".join(rst for rst in ready_sample_results))

        if unready_sample_results:
            self.respond("The results for sample(s) %(sample_id)s are "
                        "not yet ready. You will be notified when they are ready.",
                        sample_id=', '.join(str(sample_id) for sample_id in unready_sample_results))

        if unfound_sample_results:
            if len(unfound_sample_results)==1:
                self.respond("Sorry man, no sample with id %s was found for your clinic. "
                            "Please check your DBS records and try again." % sample_id)
            else:
                self.respond("Sorry, no samples with ids %(sample_id)s were found for your clinic. "
                            "Please check your DBS records and try again." ,
                            sample_id=', '.join(str(sample_id) for sample_id in unfound_sample_results))




