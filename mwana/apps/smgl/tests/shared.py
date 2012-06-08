from rapidsms.tests.harness import MockBackend
from threadless_router.router import Router
from threadless_router.tests.scripted import TestScript
from mwana.apps.smgl.models import PreRegistration
import logging
from mwana.apps.contactsplus.models import ContactType
from mwana.apps.locations.models import Location

def create_prereg_user(fname, location_code, ident, ctype, lang=None):
    if not lang:
        lang = "en"
    logging.debug('Creating Prereg Object in DB: ident:%s, contact_type:%s, lang:%s' % (ident, ctype, lang))
    pre = PreRegistration()
    pre.first_name = fname
    pre.facility_code = location_code
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
            %(num)s > join %(name)s
            %(num)s < Thank you for registering! You have successfully registered as a %(ctype)s at %(loc)s.
        """ % { "num": ident, "name": name, "ctype": type_display, "loc": place_display}
        self.runScript(script)


    def setUp(self):
        # this call is required if you want to override setUp
        super(SMGLSetUp, self).setUp()
        backends = {'mockbackend': {"ENGINE": MockBackend}}
        router = Router(backends=backends)

