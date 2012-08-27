from threadless_router.tests.scripted import TestScript
from mwana.apps.smgl.models import PreRegistration
import logging
from mwana.apps.contactsplus.models import ContactType
from mwana.apps.locations.models import Location
from mwana.apps.smgl import const
from rapidsms.models import Connection

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
    pre.language=lang
    pre.save()
    return pre

class SMGLSetUp(TestScript):

    def createUser(self, ctype, ident, name="Anton", location="804024"):
        create_prereg_user(name, location, ident, ctype, "en")
        type_display = ContactType.objects.get(slug__iexact=ctype).name
        place_display = Location.objects.get(slug__iexact=location).name
        script = """
            %(num)s > join %(name)s en
            %(num)s < Thank you for registering! You have successfully registered as a %(ctype)s at %(loc)s.
        """ % { "num": ident, "name": name, "ctype": type_display, "loc": place_display}
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