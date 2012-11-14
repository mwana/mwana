import logging
import random
import string

from datetime import datetime, timedelta

from rapidsms.models import Connection, Contact, Backend

from smsforms.models import XFormsSession, DecisionTrigger

from threadless_router.tests.scripted import TestScript

from mwana.apps.contactsplus.models import ContactType
from mwana.apps.locations.models import Location, LocationType
from mwana.apps.smgl.models import (FacilityVisit, PregnantMother,
         BirthRegistration, DeathRegistration, Referral)
from mwana.apps.smgl import const
from mwana.apps.smgl.models import PreRegistration


def create_prereg_user(fname, location_code, ident, ctype, lang=None):
    if not lang:
        lang = "en"
    logging.debug('Creating Prereg Object in DB: ident:%s, contact_type:%s, lang:%s' % (ident, ctype, lang))
    pre = PreRegistration()
    pre.first_name = fname
    pre.location = Location.objects.get(slug__iexact=location_code)
    pre.phone_number = ident
    pre.unique_id = ident.strip().strip('+')
    pre.title = ctype
    pre.language = lang
    pre.save()
    return pre


def create_instance(model, defaults, data):
    """
    Given model, defaults, data return a model instance of type 'model'
    with defaults 'defaults' overidden with data in 'data'.
    """
    defaults.update(data)
    instance = model(**defaults)
    instance.clean()
    instance.save()
    return instance


def create_location(data={}):
    name = get_random_string()
    type = LocationType.objects.get(singular="Province")
    defaults = {
        'name': name,
        'slug': name,
        'type': type,
    }
    return create_instance(Location, defaults, data)


def create_connection(data={}):
    defaults = {
        'backend': Backend.objects.get_or_create(name='mockbackend')[0],
        'identity': get_random_string(choices=string.digits),
    }
    return create_instance(Connection, defaults, data)


def create_contact(data={}):
    name = get_random_string()
    cnx = create_connection()
    defaults = {
        'name': name,
    }
    contact = create_instance(Contact, defaults, data)
    contact.connection_set.add(cnx)
    contact.save()
    return contact


def create_session(trigger, data={}):
    defaults = {
        'session_id': get_random_string(),
        'connection': create_connection(),
        'trigger': trigger,
    }
    return create_instance(XFormsSession, defaults, data)


def create_mother(data={}):
    contact = create_contact()
    name = get_random_string()
    location = Location.objects.get(slug="804030")
    defaults = {
        'first_name': name,
        'last_name': name,
        'contact': contact,
        'location': location,
        'uid': name,
        'next_visit': (datetime.now() + timedelta(days=7)).date(),
        'reason_for_visit': 'r'
    }
    return create_instance(PregnantMother, defaults, data)


def create_birth_registration(data={}):
    contact = create_contact()
    mother = create_mother(data={'contact': contact})
    trigger = DecisionTrigger.objects.get(trigger_keyword='birth')
    session = create_session(trigger=trigger,
                             data={'connection': contact.default_connection}
                             )
    defaults = {
        'contact': contact,
        'connection': contact.default_connection,
        'session': session,
        'mother': mother,
        'date': datetime.now().date(),
        'gender': 'bo',
        'place': 'f',
    }
    return create_instance(BirthRegistration, defaults, data)


def create_death_registration(data={}):
    contact = create_contact()
    mother = create_mother(data={'contact': contact})
    defaults = {
        'contact': contact,
        'connection': contact.default_connection,
        'unique_id': mother.uid,
        'date': datetime.now().date(),
        'person': 'inf',
        'place': 'fac',
    }
    return create_instance(DeathRegistration, defaults, data)


def create_facility_visit(data={}):
    contact = create_contact()
    mother = create_mother(data={'contact': contact})
    location = Location.objects.get(slug="804030")
    defaults = {
        'location': location,
        'contact': contact,
        'mother': mother,
        'visit_date': datetime.now().date(),
        'visit_type': 'anc',
        'next_visit': (datetime.now() + timedelta(days=30)).date(),
        'reason_for_visit': 'r'
    }
    return create_instance(FacilityVisit, defaults, data)


def create_referral(data={}):
    contact = create_contact()
    mother = create_mother(data={'contact': contact})
    trigger = DecisionTrigger.objects.get(trigger_keyword='refer')
    session = create_session(trigger=trigger,
                             data={'connection': contact.default_connection}
                             )
    loc_type = LocationType.objects.get(singular='Rural Health Centre')
    facility = create_location(data={'name': 'foo',
                                     'type': loc_type,
                                     }
                              )
    defaults = {
        'session': session,
        'facility': facility,
        'mother': mother,
        'date': (datetime.now() + timedelta(days=30)).date(),
    }
    return create_instance(Referral, defaults, data)


def get_random_string(length=10, choices=string.ascii_letters):
    return u''.join(random.choice(choices) for x in xrange(length))


class SMGLSetUp(TestScript):

    def setUp(self):
        # set some static dates that are useful for message generation.
        self.earlier = (datetime.now() - timedelta(days=30)).date()
        self.yesterday = (datetime.now() - timedelta(days=1)).date()
        self.tomorrow = (datetime.now() + timedelta(days=1)).date()
        self.later = (datetime.now() + timedelta(days=30)).date()
        super(SMGLSetUp, self).setUp()

    def createUser(self, ctype, ident, name="Anton", location="804024"):
        create_prereg_user(name, location, ident, ctype, "en")
        type_display = ContactType.objects.get(slug__iexact=ctype).name
        place_display = Location.objects.get(slug__iexact=location).name
        script = """
            %(num)s > join %(name)s en
            %(num)s < Thank you for registering! You have successfully registered as a %(ctype)s at %(loc)s.
        """ % {"num": ident, "name": name, "ctype": type_display, "loc": place_display}
        self.runScript(script)
        return Connection.objects.get(identity=ident).contact

    def createDefaults(self):
        create_prereg_user("AntonTN", "kalomo_district", '11', 'TN', 'en')
        create_prereg_user("AntonAD", "804030", '12', 'AM', 'en')
        create_prereg_user("AntonCW", "804030", '13', 'worker', 'en')
        create_prereg_user("AntonOther", "kalomo_district", "14", 'dmho', 'en')
        create_prereg_user("AntonDA", "804024", "15", const.CTYPE_DATACLERK, 'en')

        create_users = """
            11 > Join AntonTN EN
            11 < Thank you for registering! You have successfully registered as a Triage Nurse at Kalomo District.
            12 > join ANTONAD en
            12 < Thank you for registering! You have successfully registered as a Ambulance at Kalomo District Hospital HAHC.
            13 > join antonCW en
            13 < Thank you for registering! You have successfully registered as a Clinic Worker at Kalomo District Hospital HAHC.
            14 > join antonOther en
            14 < Thank you for registering! You have successfully registered as a District mHealth Officer at Kalomo District.
            15 > join AntonDA en
            15 < Thank you for registering! You have successfully registered as a Data Clerk at Chilala.
        """
        self.runScript(create_users)
