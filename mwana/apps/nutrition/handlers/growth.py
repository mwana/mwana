# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datetime import date
import decimal
from decimal import Decimal as D
import logging

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django import forms

from pygrowup.pygrowup import *
from people.models import PersonType, Person

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from mwana.apps.nutrition.messages import ASSESS_CONFIRM
from mwana.apps.nutrition.messages import DATA_SAVED_NO_ASSESSMENT
from mwana.apps.nutrition.messages import GARBLED_MSG
from mwana.apps.nutrition.messages import INVALID_DOB
from mwana.apps.nutrition.messages import INVALID_GENDER
from mwana.apps.nutrition.messages import INVALID_GM
from mwana.apps.nutrition.messages import INVALID_ID
from mwana.apps.nutrition.messages import INVALID_MEASUREMENT
from mwana.apps.nutrition.messages import REGISTER_BEFORE_REPORTING
from mwana.apps.nutrition.messages import REPORT_HELP
from mwana.apps.nutrition.messages import TOO_FEW_TOKENS
from mwana.apps.nutrition.messages import TOO_MANY_TOKENS

from mwana.apps.nutrition.models import Assessment
from mwana.apps.nutrition.models import Contact
from mwana.apps.nutrition.models import Survey, SurveyEntry

from mwana.apps.reminders.models import PatientEvent


logger = logging.getLogger(__name__)


class GrowthHandler(KeywordHandler):

    keyword = 'gm'

    def help(self):
        """Respond with message on how to report nutrition indicators.
        """
        self.respond(REPORT_HELP)

    def __get_or_create_patient(self, **kwargs):
        logger.debug("finding patient...")
        # Person model requires a PersonType, rather than rock the boat and
        # alter how People work, make sure that a Patient PersonType exists.
        # Also this seems sensible if this code gets refactored it will be
        # easier to port old data...
        person_type, created = PersonType.objects.get_or_create(
            singular='Patient', plural='Patients')
        kwargs.update({'type': person_type})

        try:
            # first try to look up patient using only id
            # we don't want to use bday and gender in case this is an update
            # or correction to an already known patient (get_or_create would
            # make a new patient)
            patient_args = kwargs.copy()
            logger.debug(patient_args)
            ids = ['code']
            has_ids = [id in patient_args.keys() for id in ids]
            logger.debug(has_ids)
            if False not in has_ids:
                logger.debug("has ids...")
                id_kwargs = {}
                [id_kwargs.update({id: patient_args.pop(id)}) for id in ids]
                logger.debug(id_kwargs)
                # next line should bump us into the
                # exception if we have a new kid
                patient = Person.objects.get(**id_kwargs)
                logger.debug("patient!")
                # compare reported gender and bday to data on file
                # and update + notify if necessary
                bday_on_file = patient.date_of_birth
                gender_on_file = patient.gender
                if 'gender' in patient_args.keys():
                    reported_gender = patient_args.get('gender')
                    if gender_on_file != reported_gender:
                        patient.gender = reported_gender
                        patient.save()
                if 'date_of_birth' in patient_args.keys():
                    reported_bday = patient_args.get('date_of_birth')
                    if bday_on_file != reported_bday:
                        patient.date_of_birth = reported_bday
                        patient.save()
                return patient, False
        except (ObjectDoesNotExist, IndexError):
            # patient doesnt already exist, so create with all arguments
            logger.debug("new patient!")
            patient, created = Person.objects.get_or_create(**kwargs)
            return patient, created

    def _validate_date(self, potential_date):
        """tries to validate a reported date string into a date object
        returns a standardised string format of the date object"""
        logger.debug("Validating date: %s" % potential_date)
        error_msg = INVALID_DOB % potential_date
        try:
            date_field = forms.DateField(
                input_formats=('%d%m%y', '%d/%m/%y', '%d-%m-%y',
                               '%d%m%Y', '%d/%m/%Y', '%d-%m-%Y'),
                error_messages={'invalid': error_msg})
            good_date_obj = date_field.clean(potential_date)
            if good_date_obj:
                return good_date_obj.__str__(), good_date_obj
        except ValidationError, e:
            self.respond(e[0])
            return None, None

    def _validate_sex(self, potential_sex):
        logger.debug("validate sex...")
        logger.debug(potential_sex)
        try:
            gender = helpers.get_good_sex(potential_sex)
            if gender is not None:
                return gender
            else:
                return None
        except Exception, e:
            self.exception('problem validating sex: %s' % e)

    def _validate_bool(self, potential_bool):
        logger.debug("validate bool...")
        logger.debug(potential_bool)
        try:
            if potential_bool is not None:
                if potential_bool[0].upper() in ["Y", "YES", "O", "OUI"]:
                    return "Y", 1
                elif potential_bool[0].upper() in ["N", "NO", "NON"]:
                    return "N", 0
                else:
                    return None, 0
            else:
                return None, 0
        except Exception, e:
            self.exception('problem validating bool: %s' % e)

    def _validate_ids(self, id_dict):
        logger.debug("validate ids...")
        try:
            valid_ids = {}
            invalid_ids = {}
            for k, v in id_dict.iteritems():
                if v.isdigit() or v.upper().startswith('X'):
                    valid_ids.update({k: v})
                else:
                    invalid_ids.update({k: v})
            return valid_ids, invalid_ids
        except Exception, e:
            self.exception('problem validating ids: %s' % e)

    def _validate_action_taken(self, action_taken):
        logger.debug("validate action taken ...")
        logger.debug(action_taken)
        if action_taken is not None:
            if action_taken[:2].upper() in ['NR', 'OF', 'OT', 'RG', 'SF']:
                return action_taken[:2]
            else:
                return 'XX'
        else:
            return 'XX'

    def __identify_healthworker(self):
        # return the healthworker if already registered on this connection
        try:
            healthworker = self.msg.connections[0].contact
            return healthworker
        except ObjectDoesNotExist:
            return None

    def _get_tokens(self, text):
        """Splits the text into the expected parts."""
        token_labels = ['child_id', 'date_of_birth', 'gender', 'weight',
                        'height', 'oedema', 'muac', 'action_taken']
        validate_tokens = True
        try:
            token_data = text.split()
            if len(token_data) > 8:
                logger.debug("too much data")
                self.respond(TOO_MANY_TOKENS)
                validate_tokens = False
            elif len(token_data) < 8:
                logger.debug("missing data")
                self.respond(TOO_FEW_TOKENS)
                validate_tokens = False
            return dict(zip(token_labels, token_data)), validate_tokens
        except:
            reformat_msg = GARBLED_MSG % text
            self.respond(reformat_msg)
            return None, validate_tokens

    def _validate_tokens(self, tokens):
        """Validate all tokens in the expected order."""
        errors = []
        # validate ids
        valid_ids, invalid_ids = self._validate_ids(
            {'child_id': tokens['child_id']})
        if len(invalid_ids) > 0:
            for k, v in invalid_ids.iteritems():
                errors.append(INVALID_ID % (v, k))
        if len(valid_ids) > 0:
            for k, v in valid_ids.iteritems():
                tokens.update({k: v})

        # validate date_of_birth
        dob_str, dob_obj = self._validate_date(tokens['date_of_birth'])
        if dob_obj is not None:
            if dob_obj > date.today():
                errors.append(INVALID_GM)
            tokens['date_of_birth'] = dob_obj
        else:
            errors.append(INVALID_DOB % tokens['date_of_birth'])

        # validate gender
        gender = self._validate_sex(tokens['gender'])
        if gender is not None:
            tokens['gender'] = gender
        else:
            errors.append(INVALID_GENDER % tokens['gender'])

        # validate weight
        if tokens['weight'] is not None:
            if 1.5 < float(tokens['weight']) < 35.0:
                tokens['weight'] = float(tokens['weight'])
            else:
                # do not process with invalid weight
                # but allow processing to continue
                tokens['weight'] = None

        # validate height
        if tokens['height'] is not None:
            if 40.0 < float(tokens['height']) < 125.0:
                tokens['height'] = float(tokens['height'])
            else:
                # do not process with invalid height
                # but allow processing to continue
                tokens['height'] = None

        # skip validating boolean oedema
        # validate muac, do not process invalid values but allow processing
        # to continue
        if tokens['muac'] is not None:
            if tokens['muac'].upper() in ['N']:
                tokens['muac'] = None
            elif 10.0 < float(tokens['muac']) < 22.0:
                tokens['muac'] = float(tokens['muac'])
            else:
                tokens['muac'] = None

        # validate action_taken
        tokens['action_taken'] = self._validate_action_taken(
            tokens['action_taken'])

        return tokens, errors

    def _get_who_categories(self, ass, survey):
        if ass.weight4age is not None:
            if (ass.weight4age >= D(str(3.00))):
                ass.underweight = 'V'
            elif (D(str(2.00)) <= ass.weight4age < D(str(3.00))):
                ass.underweight = 'T'
            elif (D(str(-1.00)) <= ass.weight4age < D(str(2.00))):
                ass.underweight = 'G'
            elif (D(str(-2.00)) <= ass.weight4age < D(str(-1.00))):
                ass.underweight = 'M'
            elif (D(str(-3.00)) <= ass.weight4age < D(str(-2.00))):
                ass.underweight = 'U'
            elif (ass.weight4age < D(str(-3.00))):
                ass.underweight = 'S'

        if ass.height4age is not None:
            if (ass.height4age >= D(str(-1.00))):
                ass.stunting = 'G'
            elif (D(str(-2.00)) <= ass.height4age < D(str(-1.00))):
                ass.stunting = 'M'
            elif (D(str(-3.00)) <= ass.height4age < D(str(-2.00))):
                ass.stunting = 'U'
            elif (ass.height4age < D(str(-3.00))):
                ass.stunting = 'S'

        if ass.weight4height is not None:
            if (ass.weight4height >= D(str(-1.00))):
                ass.wasting = 'G'
            elif (D(str(-2.00)) <= ass.weight4height < D(str(-1.00))):
                ass.wasting = 'M'
            elif (D(str(-3.00)) < ass.weight4height < D(str(-2.00))):
                ass.wasting = 'U'
            elif (ass.weight4height <= D(str(-3.00))):
                ass.wasting = 'S'

        if ass.muac is not None:
            if (survey.mild_muac <= ass.muac <= survey.normal_muac):
                ass.wasting = 'M'
            elif (survey.severe_muac <= ass.muac <= survey.mild_muac):
                ass.wasting = 'U'
            elif (ass.muac <= survey.severe_muac):
                ass.wasting = 'S'
            elif (ass.muac >= survey.normal_muac):
                ass.wasting = 'G'

        if (ass.weight4height is not None and ass.muac is not None):
            if (D(str(-1.0)) <= ass.weight4height):
                ass.wasting = 'G'
            if ((D(str(-2.00)) < ass.weight4height <= D(str(-1.00))) or (survey.mild_muac <= ass.muac <= survey.normal_muac)):
                ass.wasting = 'M'
            if ((D(str(-3.00)) < ass.weight4height <= D(str(-2.00))) or (survey.severe_muac <= ass.muac <= survey.mild_muac)):
                ass.wasting = 'U'
            if ((ass.weight4height < D(str(-3.00))) or (ass.muac <= survey.severe_muac)):
                ass.wasting = 'S'
        ass.save()
        return ass

    def _check_wasting(self, ass):
        """Creates a patient event for SAM if child is wasting"""
        if (ass.wasting == 'S'):
            event = "RUTF"
            # import pdb
            # pdb.set_trace()
            sam_date = date.today()
            if healthworker and healthworker.location:
                child, created = Contact.objects.get_or_create(
                    name=patient.code,
                    location=healthworker.location)
                patient_t = const.get_patient_type()
                if not child.types.filter(pk=patient_t.pk).count():
                    child.types.add(patient_t)

            # finally create the SAM event
            PatientEvent(event=event,
                         date=sam_date,
                         cba_conn=healthworker.default_connection,
                         notification_status="sam", patient=child)

    def _update_survey_averages(self, ass, survey, survey_entry, results):
        try:
            logger.debug('updating averages...')
            average_zscores = survey.update_avg_zscores()
            logger.debug(average_zscores)
            context = decimal.getcontext()
            for ind, z in results.iteritems():
                logger.debug(str(ind) + " " + str(z))
                if z is not None:
                    survey_avg = average_zscores[ind]
                    logger.debug(survey_avg)
                    # TODO plus or minus!
                    survey_avg_limit = survey.average_limit
                    if survey_avg is not None:
                        survey_avg_limit = context.add(
                            survey.average_limit, abs(survey_avg))
                    if abs(z) > survey_avg_limit:
                        logger.debug('BIG Z: ' + ind)
                        logger.debug('sample z: ' + str(z))
                        logger.debug('avg z: ' + str(survey_avg_limit))
                        # add one to healthworker's error tally
                        healthworker.errors = healthworker.errors + 1
                        healthworker.save()
                        # mark the entry and the assessment as 'suspect'
                        survey_entry.flag = 'S'
                        survey_entry.save()
                        ass.status = 'S'
                        ass.save()
                        return self.respond(INVALID_MEASUREMENT %
                                            (patient.code))
        except Exception, e:
            self.exception('problem with analysis')
            logger.error("problem with analysis: %s" % e)

    def handle(self, text):
        """Handle the gm submission."""

        try:
            survey = Survey.objects.get(
                begin_date__lte=date.today(),
                end_date__gte=date.today())
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            return self.respond("No active survey at this date")

        cg = childgrowth(False, False)

        healthworker = self.__identify_healthworker()
        if healthworker is None:
            # only registered users can report
            return self.respond(REGISTER_BEFORE_REPORTING)

        # get the tokens from the text
        tokens, validate_tokens = self._get_tokens(text)

        # don't bother saving or proceeding as there are errors
        if not validate_tokens:
            return True

        # save the raw data submission as it was sent
        survey_entry = SurveyEntry(**tokens)
        survey_entry.healthworker = healthworker
        survey_entry.save()

        # replace the "no data" shorthands
        for k, v in tokens.iteritems():
            # replace 'no data' shorthands with None
            if v.upper() in ['X', 'XX', 'XXX']:
                tokens.update({k: None})

        # validate all inputs, return tokens dict with valid data types
        # and validation errors
        data, errors = self._validate_tokens(tokens)
        if len(errors) > 0:
            # halt process if any data is not valid for further processing.
            error_msg = " ".join(errors)
            return self.respond(error_msg)

        # collect kwargs for patient
        patient_kwargs = {'code': data['child_id']}
        patient_kwargs.update({'date_of_birth': data['date_of_birth']})
        patient_kwargs.update({'gender': data['gender']})
        patient_kwargs.update({'action_taken': data['action_taken']})
        # get or create and update patient
        try:
            patient, created = self.__get_or_create_patient(**patient_kwargs)
            # update age of the patient
            patient.age_in_months = helpers.date_to_age_in_months(
                patient.date_of_birth)
            patient.save()
        except Exception:
            logger.debug('There was an error getting/creating the patient.')
            self.exception('There was an error getting/creating the patient.')

        # try to make an assessment
        try:
            human_oedema, bool_oedema = self._validate_bool(data['oedema'])
            if data['height'] or data['weight'] or data['muac']:
                ass = Assessment(
                    healthworker=healthworker, patient=patient,
                    height=data['height'],
                    weight=data['weight'],
                    muac=data['muac'], oedema=bool_oedema,
                    survey=survey, action_taken=data['action_taken'])
            else:
                logger.debug("have null values for height, weight and muac.")
                ass = Assessment(healthworker=healthworker,
                                 patient=patient,
                                 oedema=bool_oedema, survey=survey,
                                 action_taken=data['action_taken'])

            ass.save()
            logger.debug("saved assessment")
        except:
            logger.debug("could not save an assessment")
            ass = None
            return self.respond(DATA_SAVED_NO_ASSESSMENT)

        # process assessment and confirmation
        if ass is not None:
            results = ass.analyze(cg)
            logger.debug(results)
            ass = self._get_who_categories(ass, survey)

            # check for wasting
            self._check_wasting(ass)

            # update survey averages
            self._update_survey_averages(ass, survey, survey_entry, results)

            # send feedback to healthworker
            try:
                logger.debug('constructing confirmation')
                confirmation = ASSESS_CONFIRM %\
                    (healthworker.name, ass.get_wasting_display(),
                     ass.get_underweight_display(), ass.get_stunting_display())
                logger.debug('confirmation constructed')
                # send confirmation AFTER any error messages
                if confirmation is not None:
                    self.respond(confirmation)
                    logger.debug('sent confirmation')
                else:
                    logger.debug('confirmation message was not built properly')
            except Exception, e:
                logger.error('problem constructing confirmation: %s' % e)
