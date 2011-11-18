# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datetime import date, datetime
import decimal
from decimal import Decimal as D
import time
import gettext

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import F

from pygrowup.pygrowup import *
from people.models import PersonType

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from mwana.apps.nutrition.messages import *
from mwana.apps.nutrition.models import *

class ReportGMHandler(KeywordHandler):

    keyword = "gm"

    
    def help(self):
        self.respond(REPORT_HELP)

    def start(self):
        # initialize childgrowth, which loads WHO tables
        # TODO is this the best place for this??
        # TODO make childgrowth options configurable via config.py
        self.cg = childgrowth(False, False)

    def __get_or_create_patient(self, **kwargs):
        self.debug("finding patient...")
        # Person model requires a PersonType, rather than rock the boat and
        # alter how People work, make sure that a Patient PersonType exists.
        # Also this seems sensible if this code gets refactored it will be
        # easier to port old data...
        person_type, created = PersonType.objects.get_or_create(singular='Patient', plural='Patients')
        kwargs.update({'type':person_type})

        try:
            # first try to look up patient using only id
            # we don't want to use bday and gender in case this is an update
            # or correction to an already known patient (get_or_create would make
            # a new patient)
            patient_args = kwargs.copy()
            self.debug(patient_args)
            ids = ['code']
            has_ids = [patient_args.has_key(id) for id in ids]
            self.debug(has_ids)
            if False not in has_ids:
                self.debug("has ids...")
                id_kwargs = {}
                [id_kwargs.update({id : patient_args.pop(id)}) for id in ids]
                self.debug(id_kwargs)
                # next line should bump us into the exception if we have a new kid
                patient = Person.objects.get(**id_kwargs)
                self.debug("patient!")
                # compare reported gender and bday to data on file
                # and update + notify if necessary
                bday_on_file = patient.date_of_birth
                gender_on_file = patient.gender
                if patient_args.has_key('gender'):
                    reported_gender = patient_args.get('gender')
                    if gender_on_file != reported_gender:
                        patient.gender = reported_gender
                        patient.save()
                if patient_args.has_key('date_of_birth'):
                    reported_bday = patient_args.get('date_of_birth')
                    if bday_on_file != reported_bday:
                        patient.date_of_birth = reported_bday
                        patient.save()
                return patient, False
        except ObjectDoesNotExist, IndexError:
            # patient doesnt already exist, so create with all arguments
            self.debug("new patient!")
            patient, created  = Person.objects.get_or_create(**kwargs)
            return patient, created

    def _validate_date(self, potential_date):
        self.debug("validate date...")
        self.debug(potential_date)
        try:
            #matches = re.match( self.datepattern, potential_date, re.IGNORECASE)
            #self.debug(matches)
            #if matches is not None:
            #    date = matches.group(0)
            self.debug(potential_date)
            good_date_str, good_date_obj = helpers.get_good_date(potential_date)
            self.debug(good_date_str)
            return good_date_str, good_date_obj 
            #else:
            #    return None, None
        except Exception, e:
            self.exception('problem validating date')
            return None, None

    def _validate_sex(self, potential_sex):
        self.debug("validate sex...")
        self.debug(potential_sex)
        try:
            gender = helpers.get_good_sex(potential_sex)
            if gender is not None:
                return gender
            else:
                return None
        except Exception, e:
            self.exception('problem validating sex')
    
    def _validate_bool(self, potential_bool):
        self.debug("validate bool...")
        self.debug(potential_bool)
        try:
            if potential_bool is not None:
                if potential_bool[0].upper() in ["Y", "YES", "O", "OUI"]:
                    return "Y", 1
                elif potential_bool[0].upper() in ["N", "NO", "NON"]:
                    return "N", 0
                else:
                    return None
            else:
                return None, 0
        except Exception, e:
            self.exception('problem validating bool')

    def _validate_ids(self, id_dict):
        self.debug("validate ids...")
        try:
            valid_ids = {}
            invalid_ids = {}
            for k,v in id_dict.iteritems():
                if v.isdigit() or v.upper().startswith('X'):
                    valid_ids.update({k:v})
                else:
                    invalid_ids.update({k:v})
            return valid_ids, invalid_ids
        except Exception, e:
            self.exception('problem validating ids')

    def _validate_measurements(self, height, weight, muac):
        self.debug("validate measurements...")
        valid_height = False
        valid_weight = False
        valid_muac = False
        try:
            if height is not None:
                if 40.0 < float(height) < 125.0:
                    valid_height = True
            else:
                valid_height = True
            if weight is not None:
                if 1.5 < float(weight) < 35.0:
                    valid_weight = True
            else:
                valid_weight = True 
            if muac is not None:
                if muac in ['n','N']:
                    valid_muac = True
                elif 10.0 < float(muac) < 22.0:
                    valid_muac = True
            else:
                valid_muac = True
            return valid_height, valid_weight, valid_muac
        except Exception, e:
            self.exception('problem validating measurements')

    def __identify_healthworker(self):
        # if healthworker is already registered on this connection, return him/her
        try:
            healthworker = self.msg.connection.contact
            return healthworker
        except ObjectDoesNotExist:
            return None

    def handle(self, text):
        self.debug("reporting...")
        try:
            survey = Survey.objects.get(begin_date__lte=datetime.now().date(),\
                end_date__gte=datetime.now().date())

        except ObjectDoesNotExist, MultipleObjectsReturned:
            return self.respond("No active survey at this date")

        self.debug("initialising separate childgrowth instance..")
        cg = childgrowth(False, False)

        # find out who is submitting this report
        healthworker = self.__identify_healthworker()

        if healthworker is None:
            # halt reporting process and tell sender to register first
            return self.respond(REGISTER_BEFORE_REPORTING)

        PATTERN = re.compile(r'(?P<child_id>\d+)\s+(?P<gender>[M|F])\s+(?P<date_of_birth>\d{6})\D*(?P<weight>\d{2}\.\d{1})\D*(?P<height>\d{2}\.\d{1})\D*(?P<oedema>[Y|N])\D*(?P<muac>\d{2}\.\d{1})', re.IGNORECASE)

        token_labels = ['child_id', 'date_of_birth', 'gender', 'weight', 'height', 'oedema', 'muac']

        token_data = text.split()
        
        try:
            if len(token_data) > 7:
                self.debug("too much data")
                self.respond(TOO_MANY_TOKENS)

            tokens = dict(zip(token_labels, token_data))

            for k, v in tokens.iteritems():
                # replace 'no data' shorthands with None
                if v.upper() in ['X', 'XX', 'XXX']:
                    tokens.update({k : None})

            # save record of survey submission before doing any processing
            # so we have all of the entries as they were submitted
            survey_entry = SurveyEntry(**tokens)
            survey_entry.healthworker = healthworker
            # save age in months for raw data as well
            raw_dob_str, raw_dob_obj = self._validate_date(survey_entry.date_of_birth)
            if raw_dob_obj is not None:
                survey_entry.age_in_months = helpers.date_to_age_in_months(raw_dob_obj)
            survey_entry.save()
        except Exception, e:
            self.exception()
            self.respond(INVALID_MEASUREMENT %\
                (survey_entry.child_id))

        # check that id codes are numbers
        valid_ids, invalid_ids = self._validate_ids(
            {'child' : survey_entry.child_id})
        # send responses for each invalid id, if any
        if len(invalid_ids) > 0:
            for k,v in invalid_ids.iteritems():
                self.respond(INVALID_ID % (v, k))
            # halt reporting process if any of the id codes are invalid
            return True

        for k,v in valid_ids.iteritems():
            # replace 'no data' shorthands with None
            if v.upper().startswith('X'):
                tokens.update({k : None})

        self.debug("getting patient...")
        # begin collecting valid patient arguments
        patient_kwargs = {'code' : survey_entry.child_id}

        # no submitted bday
        if survey_entry.date_of_birth is None:
            patient_kwargs.update({'date_of_birth' : None})
        # make sure submitted bday is valid
        else:
            dob_str, dob_obj = self._validate_date(survey_entry.date_of_birth)
            if dob_obj is not None:
                self.debug(dob_obj)
                patient_kwargs.update({'date_of_birth' : dob_obj})
            else:
                patient_kwargs.update({'date_of_birth' : ""})
                self.respond(INVALID_DOB % (survey_entry.date_of_birth))

        # make sure reported gender is valid
        good_sex = self._validate_sex(survey_entry.gender)
        if good_sex is not None:
            self.debug(good_sex)
            patient_kwargs.update({'gender' : good_sex})
        else:
            patient_kwargs.update({'gender' : ""}) 
            # halt reporting process if we dont have a valid gender.
            # this can't be unknown. check in their pants if you arent sure
            return self.respond(INVALID_GENDER % (survey_entry.gender))

        try:
            # find patient or create a new one
            self.debug(patient_kwargs)
            patient, created = self.__get_or_create_patient(**patient_kwargs)
        except Exception, e:
            self.exception('problem saving patient')

        # we must have a patient to update
        if patient is not None:
            try:
                # update age separately (should be the only volitile piece of info)
                self.debug(survey_entry.age_in_months)
                if survey_entry.age_in_months is not None:
                    patient.age_in_months = int(survey_entry.age_in_months)
                else:
                    patient.age_in_months = helpers.date_to_age_in_months(patient.date_of_birth)
                self.debug(patient.age_in_months)
                patient.save()
            except Exception, e:
                self.exception('problem saving age')
                return self.respond("There was a problem saving the age.")

        # calculate age based on reported date of birth
        # respond if calcualted age differs from reported age
        # by more than 3 months TODO make this configurable
        #self.debug("getting sloppy age...")
        #sloppy_age_in_months = helpers.date_to_age_in_months(patient.date_of_birth)
        #self.debug(sloppy_age_in_months)
        #if (abs(int(sloppy_age_in_months) - int(patient.age_in_months)) > 3):
        #    message.respond("Date of birth indicates Child ID %s's age (in months) is %s, which does not match the reported age (in months) of %s" % (patient.code, sloppy_age_in_months, patient.age_in_months))

        try:
            self.debug("making assessment...")
            # create nutritional assessment entry
            self.debug(survey_entry.height)
            self.debug(survey_entry.weight)
            self.debug(survey_entry.muac)

            measurements = {"height" : survey_entry.height,\
                "weight" : survey_entry.weight, "muac" : survey_entry.muac}
            
            human_oedema, bool_oedema = self._validate_bool(survey_entry.oedema)
            valid_height, valid_weight, valid_muac = self._validate_measurements(\
                measurements['height'], measurements['weight'], measurements['muac'])

            self.debug(valid_height)
            self.debug(valid_weight)
            self.debug(valid_muac)

            if valid_height or valid_weight or valid_muac:
                ass = Assessment(healthworker=healthworker, patient=patient,\
                        height=measurements['height'], weight=measurements['weight'],\
                        muac=measurements['muac'], oedema=bool_oedema, survey=survey)
            else:
                self.debug("have null values for height, weight and muac.")
                ass = Assessment(healthworker=healthworker, patient=patient,\
                             oedema=bool_oedema, survey=survey)

            ass.save()
            self.debug("saved assessment")
        except Exception, e:
            self.exception("problem making assessment")
            self.respond(INVALID_MEASUREMENT % (survey_entry.child_id))



        try:
            data = [
                    "ChildID=%s"  % (patient.code or "??"),
                    "Gender=%s"      % (patient.gender or "??"),
                    "DOB=%s"        % (patient.date_of_birth or "??"),
                    "Age=%sm"      % (patient.age_in_months or "??"),
                    "Weight=%skg"   % (measurements['weight'] or "??"),
                    "Height=%scm"  % (measurements['height'] or "??"),
                    "Oedema=%s"   % (human_oedema or "??"),
                    "MUAC=%scm"      % (measurements['muac'] or "??")]

            self.debug('constructing confirmation')
            confirmation = REPORT_CONFIRM %\
                (healthworker.name, " ".join(data))
            self.debug('confirmation constructed')
        except Exception, e:
            self.exception('problem constructing confirmation')

        try:
            # perform analysis based on cg instance from start()
            # TODO add to Assessment save method?
            if ass is not None:
                results = ass.analyze(cg)
                self.debug('assessment analyzed!')
                self.debug(results)
                # categorise child status based on results of zscores.
                if ass.weight4age is not None:
                    if (ass.weight4age >= D(str(3.00))):
                        ass.underweight = 'V'
                    elif (D(str(2.00)) <= ass.weight4age < D(str(3.00))):
                        ass.underweight = 'T'
                    elif (D(str(0.00)) <= ass.weight4age < D(str(2.00))):
                        ass.underweight = 'G'
                    elif (D(str(-1.00)) <= ass.weight4age < D(str(0.00))):
                        ass.underweight = 'L'
                    elif (D(str(-2.00)) <= ass.weight4age < D(str(-1.00))):
                        ass.underweight = 'M'
                    elif (D(str(-3.00)) <= ass.weight4age < D(str(-2.00))):
                        ass.underweight = 'U'
                    elif (ass.weight4age < D(str(-3.00))):
                        ass.underweight = 'S'

                if ass.height4age is not None:
                    if (ass.height4age >= D(str(3.0))):
                        ass.stunting = 'V'
                    elif (D(str(2.00)) <= ass.height4age < D(str(3.00))):
                        ass.stunting = 'T'
                    elif (D(str(0.00)) <= ass.height4age < D(str(2.00))):
                        ass.stunting = 'G'
                    elif (D(str(-1.0)) <= ass.height4age < D(str(0.00))):
                        ass.stunting = 'L'
                    elif (D(str(-2.00)) <= ass.height4age < D(str(-1.00))):
                        ass.stunting = 'M'
                    elif (D(str(-3.00)) <= ass.height4age < D(str(-2.00))):
                        ass.stunting = 'U'
                    elif (ass.height4age < D(str(-3.00))):
                        ass.stunting = 'S'

                if (ass.weight4height is not None and ass.muac is not None):
                    if (ass.weight4height >= D(str(3.0))):
                        ass.wasting = 'V'
                    if (D(str(2.00)) <= ass.weight4height < D(str(3.00))):
                        ass.wasting = 'T'
                    if (D(str(0.00)) <= ass.weight4height < D(str(2.00))):
                        ass.wasting = 'G'
                    if (D(str(-1.0)) <= ass.weight4height < D(str(0.00))):
                        ass.wasting = 'L'
                    if ((D(str(-2.00)) < ass.weight4height <= D(str(-1.00))) or (12.51 <= ass.muac <= 13.50) ):
                        ass.wasting = 'M'
                    if ((D(str(-3.00)) < ass.weight4height <= D(str(-2.00))) or (11.60 <= ass.muac <= 12.50 )):
                        ass.wasting = 'U'
                    if ((ass.weight4height < D(str(-3.00))) or (ass.muac <= 11.59)):
                        ass.wasting = 'S'
                elif ass.weight4height is not None:
                    if (ass.weight4height >= D(str(3.0))):
                        ass.wasting = 'V'
                    elif (D(str(2.00)) <= ass.weight4height < D(str(3.00))):
                        ass.wasting = 'T'
                    elif (D(str(0.00)) <= ass.weight4height < D(str(2.00))):
                        ass.wasting = 'G'
                    elif (D(str(-1.0)) <= ass.weight4height < D(str(0.00))):
                        ass.wasting = 'L'
                    elif (D(str(-2.00)) <= ass.weight4height < D(str(-1.00))):
                        ass.wasting = 'M'
                    elif (D(str(-3.00)) < ass.weight4height < D(str(-2.00))):
                        ass.wasting = 'U'
                    elif (ass.weight4height <= D(str(-3.00))):
                        ass.wasting = 'S'
                elif ass.muac is not None:
                    if (12.51 <= ass.muac <= 13.50):
                        ass.wasting = 'M'
                    elif (11.60 <= ass.muac <= 12.50 ):
                        ass.wasting = 'U'
                    elif (ass.muac <= 11.59):
                        ass.wasting = 'S'

                ass.save()

            else:
                self.debug('there is no assessment saved to analyse')
            #response_map = {
            #    'weight4age'    : 'Oops. I think weight or age is incorrect',
            #    'height4age'    : 'Oops. I think height or age is incorrect',
            #    'weight4height' : 'Oops. I think weight or height is incorrect'
            #}
            self.debug('updating averages...')
            average_zscores = survey.update_avg_zscores()
            self.debug(average_zscores)
            context = decimal.getcontext()
            for ind, z in results.iteritems():
                self.debug(str(ind) + " " + str(z))
                if z is not None:
                    survey_avg = average_zscores[ind]
                    # TODO plus or minus!
                    survey_avg_limit = D(3)
                    if survey_avg is not None:
                        survey_avg_limit = context.add(D(3), abs(survey_avg))
                    if abs(z) > survey_avg_limit:
                        self.debug('BIG Z: ' + ind)
                        self.debug('sample z: ' + str(z))
                        self.debug('avg z: ' + str(survey_avg_limit))
                        # add one to healthworker's error tally
                        healthworker.errors = healthworker.errors + 1
                        healthworker.save()
                        # mark both the entry and the assessment as 'suspect'
                        survey_entry.flag = 'S'
                        survey_entry.save()
                        ass.status = 'S'
                        ass.save()
                        #message.respond(response_map[ind])
                        return self.respond(INVALID_MEASUREMENT %\
                            (patient.code))
        except Exception, e:
            self.exception('problem with analysis')

        # send confirmation AFTER any error messages
        if confirmation is not None:
            self.respond(confirmation)
            self.debug('sent confirmation')
        else:
            self.debug('there was a problem building the confirmation message')
