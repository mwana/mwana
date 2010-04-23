#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import re
from mwana.apps.labresults.models import Result
from rapidsms.contrib.handlers import KeywordHandler

UNGREGISTERED = "Sorry, you must be registered with Results160 to report DBS "
"samples sent. If you think this message is a mistake, respond with keyword 'HELP'"
HELP          = "To request for results for a DBS sample, send RESULT <sampleid>. "
"E.g result ID45"
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

    keyword = "result|results"
    PATTERN = re.compile(r'^(\s*)(\S+)$')

    def help(self):
        self.respond(HELP)

    def handle(self, text):

        if not self.msg.contact:
            self.respond(UNGREGISTERED)
            return

        if not self.PATTERN.match(text):
            if " " in text.strip():
                self.respond("The sample id must not have spaces in between. %s"% HELP)
            else:
                self.respond("%s %s" % (SORRY, HELP))
            return
        sample_id = text.strip()
        sample_results=[]
        try:
            results = Result.objects.filter(sample_id__iexact=sample_id, clinic=self.msg.contact.location)
            if results:
                for result in results:
                    if result.result and len(result.result.strip()) > 0:
                        sample_results.append("%s: %s" % (result.sample_id, result.get_result_display()))
                    else:
                        self.respond("The results for sample %(sample_id)s are "
                        "not yet ready. You will be notified when they are ready.", sample_id=sample_id)
            else:
                self.respond("Sory, no sample with id %s was found for your clinic. "
                "Please check your DBS records and try again." % sample_id)
        except Exception, e:
            self.error(e)
        if sample_results:
            self.respond(",".join( rst for rst in sample_results))


