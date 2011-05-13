# vim: ai ts=4 sts=4 et sw=4
import re
from datetime import datetime
from django.conf import settings
from django.db.models import Q
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.labresults.models import Result
from mwana import const

UNGREGISTERED = "Sorry, you must be registered with Results160 to receive DBS \
results. If you think this message is a mistake, respond with keyword 'HELP'"
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

    def _get_results(self, clinic, requisition_id):
        if settings.SEND_LIVE_LABRESULTS:
            requisition_id = Result.clean_req_id(requisition_id)
            q = Q(requisition_id_search__iexact=requisition_id) 
            if requisition_id.startswith(clinic.slug):
                short_id = re.sub('^%s' % clinic.slug, '', requisition_id)
                q |= Q(requisition_id_search__iexact=short_id)
            else:
                long_id = clinic.slug + requisition_id
                q |= Q(requisition_id_search__iexact=long_id)
            q &= Q(clinic=clinic) & Q(clinic__send_live_results=True)
            q &= Q(verified__isnull=True) | Q(verified=True)
            return Result.objects.order_by('pk').filter(q)
        else:
            return Result.objects.none()

    def is_sentence(self, text):
        alphabet = 'aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ'
        found = 0
        for char in text:
            if char in alphabet:
                found += 1
        if found > 5:
            return True
        return False
    
    def handle(self, text):
        text = text.strip()
        if not self.msg.contact:
            self.respond(UNGREGISTERED)
            return
        if self.is_sentence(text):
            self.respond("%s Send the keyword HELP if you need to be helped." % (SORRY))
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
            results = self._get_results(self.msg.contact.location,
                                        requisition_id)
            fake_id = getattr(settings, 'RESULTS160_FAKE_ID_FORMAT',
                              '{id:04d}')
            if self.msg.contact.location.type.slug in const.ZONE_SLUGS:
                clinic_id = self.msg.contact.location.parent.slug
            else:
                clinic_id = self.msg.contact.location.slug
            fake_id = fake_id.format(clinic=clinic_id, id=9999)
            fake_ids = [fake_id]
            if fake_id.startswith(clinic_id):
                fake_ids.append(fake_id[len(clinic_id):])
            fake_ids = [Result.clean_req_id(id) for id in fake_ids]
            if len(requisition_ids) == 1 and not results and\
              Result.clean_req_id(requisition_id) in fake_ids:
                # demo functionality - if '9999' was specified and no results
                # were found with that requisition ID, return a sample result
                results_text = getattr(settings, 'RESULTS160_RESULT_DISPLAY',
                                       {})
                self.respond("Sample {id}: {result}. Please record these "
                             "results in your clinic records and promptly "
                             "delete them from your phone. Thanks again".format(
                             result=results_text.get('P', 'Detected'),
                             id=fake_id))
                return
            elif results:
                for result in results:
                    if result.result and len(result.result.strip()) > 0:
                        reply = result.get_result_text()
                        ready_sample_results.append(
                                "%(req_id)s;%(res)s" %
                                {'req_id':result.requisition_id,
                                'res':reply})
                        result.notification_status = "sent"
                        if not result.result_sent_date:
                            result.result_sent_date = datetime.now()
                        result.save()
                    else:
                        unready_sample_results.append(requisition_id)
            else:
                unfound_sample_results.append(requisition_id)
        if ready_sample_results:
            resultsmsg = ". ".join("**** "+rst for rst in ready_sample_results)
            self.respond("%s. Please record these results in your clinic records and"
            " promptly delete them from your phone. Thanks again" % resultsmsg)

        if unready_sample_results:
            unready_sample_results = set(unready_sample_results)
            self.respond("The results for sample(s) %(requisition_id)s are "
                        "not yet ready. You will be notified when they are ready.",
                        requisition_id=', '.join(str(requisition_id) for requisition_id in unready_sample_results))

        if unfound_sample_results:
            unfound_sample_results = set(unfound_sample_results)
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
