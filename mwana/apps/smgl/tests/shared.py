from rapidsms.tests.harness import MockBackend
from threadless_router.router import Router
from threadless_router.tests.scripted import TestScript
from mwana.apps.smgl.models import PreRegistration
import logging

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

    def createUser(self, ctype, ident):
        create_prereg_user("Anton", "403029", ident, ctype, "en")
        script = """
            %s > join Anton
        """ % ident
        self.runScript(script)


    def setUp(self):
        # this call is required if you want to override setUp
        super(SMGLSetUp, self).setUp()
        backends = {'mockbackend': {"ENGINE": MockBackend}}
        router = Router(backends=backends)

