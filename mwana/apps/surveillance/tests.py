# vim: ai ts=4 sts=4 et sw=4
from decimal import Decimal
from mwana.apps.surveillance.models import Source
from mwana.apps.surveillance.models import Alias
from mwana.apps.surveillance.models import Report
from mwana.apps.surveillance.models import Incident

from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from mwana.apps.locations.models import Location, LocationType

from mwana import const


class TestApp(TestScript):
    def setUp(self):
        super(TestApp, self).setUp()
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        dst = LocationType.objects.create(slug=const.DISTRICT_SLUGS[0])
        prv = LocationType.objects.create(slug=const.PROVINCE_SLUGS[0])
        self.kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        self.central_clinic = Location.objects.create(name="Central Clinic",
                                                 slug="403012", type=ctr)
        self.mansa = Location.objects.create(name="Mansa",
                                        slug="403000", type=dst)
        self.luapula = Location.objects.create(name="Luapula",
                                          slug="400000", type=prv)
        script = """
            rb     > join clinic kdh rupiah banda 1234
            tk     > join clinic kdh tizie kays 1000
            """

        self.runScript(script)

    def tearDown(self):
        super(TestApp, self).tearDown()
        Contact.objects.all().delete()
#        Report.objects.all().delete()

class TestIncindetReport(TestApp):

    def test_default_responses(self):        

        script = """
            rb > case
            rb < To report cases, send CASE <DATE or WEEK_OF_YEAR> <CASE-1> <VALUE-1>, <CASE-2> <VALUE-2>, e.g. CASE 17 10 2013, TB 12, D20 12. or Case 44, TB 12, D20 12
            unknown > case DG99 100
            unknown < Sorry, you must be registered with Results160 before you can start reporting cases. Reply with HELP if you need assistance.
        """

        self.runScript(script)
        
        self.assertEqual(Source.objects.count(), 0)

    def test_new_incident(self):
        self.assertEqual(Incident.objects.count(), 0)
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(Alias.objects.count(), 0)

        script = """
            rb > case 10 10 2013, malaria 10, cholera=12
            rb < Thank you Rupiah Banda for the report.
            rb > case 40, malaria 11
            rb < Thank you Rupiah Banda for the report.
        """
        self.runScript(script)

        self.assertEqual(Incident.objects.count(), 2)
        self.assertEqual(Report.objects.count(), 3, Report.objects.all())
        self.assertEqual(Alias.objects.count(), 2)

        self.assertEqual(Report.objects.filter(incident__name__iexact='malaria', value=10).count(), 1)
        self.assertEqual(Report.objects.filter(incident__name__iexact='malaria', value=11).count(), 1)
        self.assertEqual(Report.objects.filter(incident__name__iexact='cholera', value=12).count(), 1)

        self.assertEqual(Alias.objects.filter(name__iexact='malaria').count(), 1)
        self.assertEqual(Alias.objects.filter(name__iexact='cholera').count(), 1)

    def test_existing_incident(self):
        self.assertEqual(Incident.objects.count(), 0)
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(Alias.objects.count(), 0)

        Incident.objects.create(name="Malaria", indicator_id='Mal')

        script = """
            rb > case 10 10 2013, malaria=12,
            rb < Thank you Rupiah Banda for the report.
            rb > case 40, mal 11
            rb < Thank you Rupiah Banda for the report.
        """
        self.runScript(script)

        self.assertEqual(Incident.objects.count(), 1, Incident.objects.all())
        self.assertEqual(Report.objects.count(), 2, Report.objects.all())
        self.assertEqual(Alias.objects.count(), 2)

        self.assertEqual(Report.objects.filter(incident__name__iexact='malaria', value=12).count(), 1)
        self.assertEqual(Report.objects.filter(incident__name__iexact='malaria', value=11).count(), 1)

        self.assertEqual(Alias.objects.filter(incident__name__iexact='malaria').count(), 2)

    def test_handling_multiple_incidents(self):
        self.assertEqual(Incident.objects.count(), 0)
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(Alias.objects.count(), 0)
        self.assertEqual(Source.objects.count(), 0)

        script = """
            rb > case 10 10 2013, malaria 10, cholera=12, TB
            rb < Thank you Rupiah Banda for the report.
            rb > case 40, malaria 11, BP
            rb < Thank you Rupiah Banda for the report.
        """
        self.runScript(script)

        self.assertEqual(Incident.objects.count(), 2, Incident.objects.all())
        self.assertEqual(Report.objects.count(), 3, Report.objects.all())
        self.assertEqual(Alias.objects.count(), 2)
        self.assertEqual(Source.objects.count(), 2)
        self.assertEqual(Source.objects.filter(parsed=Decimal('0.5')).count(), 1)
        self.assertEqual(Source.objects.filter(parsed=Decimal('0.667')).count(), 1)

        self.assertEqual(Report.objects.filter(incident__name__iexact='malaria', value=10).count(), 1)
        self.assertEqual(Report.objects.filter(incident__name__iexact='malaria', value=11).count(), 1)
        self.assertEqual(Report.objects.filter(incident__name__iexact='cholera', value=12).count(), 1)

        self.assertEqual(Alias.objects.filter(name__iexact='malaria').count(), 1)
        self.assertEqual(Alias.objects.filter(name__iexact='cholera').count(), 1)
