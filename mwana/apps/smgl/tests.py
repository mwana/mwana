from datetime import date
from datetime import timedelta
from rapidsms.models import Contact
from rapidsms.tests.harness import MockBackend
from threadless_router.router import Router
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from mwana.apps.reminders.models import Event
from mwana.apps.contactsplus.models import ContactType
from threadless_router.tests.scripted import TestScript
from mwana.apps.smgl.app import USER_SUCCESS_REGISTERED
from mwana.apps.smgl.models import PreRegistration

def _create_prereg_user(fname, location_code, ident, ctype, lang=None):
    pre = PreRegistration()
    pre.first_name = fname
    pre.facility_code = location_code
    pre.phone_number = ident
    pre.unique_id = ident.strip().strip('+')
    pre.title = ctype
    if lang:
        pre.language=lang
    else:
        pre.langauge="en"
    pre.save()
    return pre



class SMGLSetUp(TestScript):

    def createUser(self, ctype, ident):
        pre_reg = _create_prereg_user("Anton", "403029", ident, ctype, "en")
        script = """
            %s > join Anton
        """ % ident
        self.runScript(script)


    def setUp(self):
        # this call is required if you want to override setUp
        super(SMGLSetUp, self).setUp()
        backends = {'mockbackend': {"ENGINE": MockBackend}}
        router = Router(backends=backends)
        #Create the bare locations and locationtypes required for testing the smgl app
#        self.type_uhc = LocationType.objects.get_or_create(singular="clinic", plural="uhc", slug='uhc')[0]
#        self.type_rhc = LocationType.objects.get_or_create(singular="clinic", plural="rhc", slug='rhc')[0]
#        self.type_district = LocationType.objects.get_or_create(singular="district", plural="districts", slug="districts")[0]
#        self.type_province = LocationType.objects.get_or_create(singular="province", plural="provinces", slug="provinces")[0]
#        self.southern_province = Location.objects.create(type=self.type_province, name="Southern Province", slug="400000")
#        self.kalomo_district = Location.objects.create(type=self.type_district, name="Kalomo District", slug="403000", parent=self.southern_province)
#        self.kalomo_uhc = Location.objects.create(type=self.type_uhc, name="Kalomo UHC", slug="404000", parent=self.kalomo_district)
#        self.chilele = Location.objects.create(type=self.type_rhc, name="Chilele Clinic", slug="403029", parent=self.kalomo_uhc, send_live_results=True)
#        self.zimba_uhc = Location.objects.create(type=self.type_uhc, name="Zimba UHC", slug="403012", parent=self.kalomo_district, send_live_results=True)
#
#        #create the contact types we'll use
#        self.ctype_tn = ContactType.objects.get_or_create(name="Triage Nurse", slug="TN")[0]
#        self.ctype_cba = ContactType.objects.get_or_create(name="Community Based Agent", slug="CBA")[0]
#        self.ctype_dmho = ContactType.objects.get_or_create(name="District mHealth Officer", slug="dmho")[0]
#        self.ctype_amb = ContactType.objects.get_or_create(name="Ambulance", slug="am")[0]
#        self.ctype_smgladmin = ContactType.objects.get_or_create(name="SMGL Super User", slug="smgl")[0]

class SMGLJoinTest(SMGLSetUp):
    fixtures = ["initial_data.json"]
    def testCreateUser(self):
        pre_reg = _create_prereg_user("Anton", "chilala", "11", "TN", "en")
        script = """
            11 > join Anton
            11 < %s

        """ % (USER_SUCCESS_REGISTERED % {"name" : "Anton", "readable_user_type": "Triage Nurse",
                                          "facility": "Chilala"}) #TODO:Is this bad testing style?
        self.runScript(script)

        script = """
            11 > join Anton
            11 < Anton, you are already registered as a Triage Nurse at Chilala but your details have been updated
        """
        self.runScript(script)

    def testNotPreRegd(self):
        script = """
            12 > join Foo
            12 < Sorry, you are not on the pre-registered users list. Please contact ZCAHRD for assistance
        """
        self.runScript(script)

    def testCreateUserOtherLang(self):
        pre_reg = _create_prereg_user("Anton", "chilala", "11", "TN", "en")
        script = """
            11 > join Anton TO
            11 < %s

        """ % (USER_SUCCESS_REGISTERED % {"name" : "Anton", "readable_user_type": "Triage Nurse",
                                          "facility": "Chilala"}) #TODO:Is this bad testing style?
        self.runScript(script)
        c = Contact.objects.get(connection__identity="11")
        self.assertEqual(c.language, "TO", "Language in Contact object should be set to \"TO\"")



class SMGLAmbulanceTest(SMGLSetUp):
    def setUp(self):
        # this call is required if you want to override setUp
        super(SMGLSetUp, self).setUp()


#    def testDhoEidAndBirthReports(self):
##        self.assertEqual(0, DhoReportNotification.objects.count())
#        Event.objects.create(name="Birth", slug="birth")
#
#        today = date.today()
#        month_ago = date(today.year, today.month, 1)-timedelta(days=1)
#
#        script = """
#            cba > birth 2 %(last_month)s %(last_month_year)s unicef innovation
#            cba > birth 4 %(last_month)s %(last_month_year)s unicef innovation
#            cba < some_stuff
#        """ % {"last_month":month_ago.month, "last_month_year":month_ago.year}
#        self.runScript(script)


