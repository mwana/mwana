import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from rapidsms.router import send
from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.models import Contact

from mwana import const
from mwana.apps.stringcleaning.inputcleaner import InputCleaner

from mwana.apps.labresults.models import Result
from mwana.apps.labresults.models import EIDConfirmation

from mwana.apps.labresults.messages import EID_HELP
from mwana.apps.labresults.messages import REGISTER_AS_CLINIC


logger = logging.getLogger(__name__)


class EIDHandler(KeywordHandler):
    """Handles reports on DBS results delivered to clients at the clinic.

       EID <SAMPLE_ID> <HIV> <ACTION_TAKEN ART/CPT> <AGE AT ART/CPT> <ART_NUMBER>
    """

    keyword = "eid"

    def help(self):
        self.respond(EID_HELP)

    def _clean_text(self, text):
        """Cleans text and sends tokens for validation. """
        cleaner = InputCleaner()
        text = cleaner.remove_dash_plus(text)
        text = cleaner.remove_double_spaces(text)
        labels = ['sample', 'status', 'action_taken', 'age_in_months',
                  'art_number']
        data = text.split()
        if len(data) == 5:
            tokens = dict(zip(labels, data))
            tokens, error_msg, errors = self._validate_tokens(tokens)
            return tokens, errors, error_msg
        if len(data) == 4:
            data.append('None')
            tokens = dict(zip(labels, data))
            tokens, error_msg, errors = self._validate_tokens(tokens)
            return tokens, errors, error_msg
        else:
            self.help()

    def _validate_tokens(self, tokens):
        """Checks the validity of each token by its type."""
        errors = False
        error_msg = "Sorry. "

        # validate sample, can't really, vary too much to start

        # validate status
        if tokens['status'].upper() in ['P', 'N', 'U']:
            pass
        else:
            error_msg += "Valid status is P, N or U. "

        # validate action taken
        if tokens['action_taken'].upper() in ["ART", "CPT"]:
            pass
        else:
            error_msg += "Valid actions are ART or CPT. "

        # validate age

        return tokens, error_msg, errors

    def _identify_healthworker(self):
        """Return the healthworker if registered on this
           connection otherwise return false.
        """
        try:
            if self.msg.connections[0].contact is not None:
                clinic_worker = self.msg.connections[0].contact
                return clinic_worker
            else:
                return None
        except ObjectDoesNotExist:
                return None

    def _is_clinic_worker(self, hworker):
        clinic_workers = Contact.active.filter(
            Q(location=hworker.clinic) | Q(location__parent=hworker.clinic),
            Q(types=const.get_clinic_worker_type())).distinct().order_by('pk')
        # shouldbe better to check the location using the sample id's location code
        if hworker in clinic_workers:
            return hworker
        else:
            return None

    def handle(self, text):
        # check if reporter is legit
        healthworker = self._identify_healthworker()
        if healthworker is None:
            return self.respond(REGISTER_AS_CLINIC)
        clinic_worker = self._is_clinic_worker(healthworker)
        if clinic_worker is None:
            return self.respond(REGISTER_AS_CLINIC)
        # clean incoming text and validate tokens
        text = text.strip()
        tokens, errors, error_msg = self._clean_text(text)

        if errors:
            send(error_msg, clinic_worker.default_connection)
            return False

        eid_confirmation = EIDConfirmation(**tokens)
        eid_confirmation.contact = clinic_worker
        eid_confirmation.save()
        logger.debug("saved eid delivery confirmation")

        # check if result is in the database
        results = Result.objects.filter(requisition_id_search=tokens['sample'])
        if len(results) > 0:
            eid_confirmation.result = results[0]
            eid_confirmation.save()

        # construct response
        confirmation = "Thank you for delivering the result for sample %s to\
        the client." % (tokens['sample'])

        # send back response
        send(confirmation, [clinic_worker.default_connection])
