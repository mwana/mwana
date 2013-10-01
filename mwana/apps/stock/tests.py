# vim: ai ts=4 sts=4 et sw=4
from datetime import timedelta
from mwana.apps.stock.models import Stock
from mwana.apps.stock.models import StockAccount
from datetime import date

from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from mwana.apps.locations.models import Location, LocationType

from mwana import const

from mwana.apps.stock.models import Threshold

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
        mansa = Location.objects.create(name="Mansa",
                                        slug="403000", type=dst)
        luapula = Location.objects.create(name="Luapula",
                                          slug="400000", type=prv)
        script = """
            lost   > join
            lost   < To register, send JOIN <TYPE> <LOCATION CODE> <NAME> <PIN CODE>
            rb     > join clinic kdh rupiah banda 123q
            rb     < Sorry, 123q wasn't a valid pin code. Please make sure your code is a 4-digit number like 1234. Send JOIN <TYPE> <LOCATION CODE> <YOUR NAME> <PIN CODE>.
            tk     > join clinic kdh tizie kays -1000"""

        self.runScript(script)

    def tearDown(self):
        super(TestApp, self).tearDown()
        Contact.objects.all().delete()
        Threshold.objects.all().delete()
        
    def test_threshold_addition(self):
        self.assertEqual(Threshold.objects.count(), 0)

        stock = Stock.objects.create(abbr='DRG-123', code='DRG_123', name='My Drug')
        self.assertEqual(Stock.objects.all().count(), 1)

        acc = StockAccount()
        acc.location = self.central_clinic
        acc.stock = stock
        acc.save()
        self.assertEqual(StockAccount.objects.all().count(), 1)

        acc2 = StockAccount.objects.create(stock=stock, location=self.kdh)

        t = Threshold()
        t.level = 6
        t.account = acc
        t.start_date = date.today() - timedelta(days=5)

        t.save()

        self.assertEqual(Threshold.objects.all().count(), 1)
        self.assertEqual(Threshold.objects.filter(end_date=None).count(), 1)



        t2 = Threshold.objects.create(level=12, account=acc)
        control= Threshold.objects.create(level=2, account=acc2)
        self.assertEqual(Threshold.objects.all().count(), 3)
        self.assertEqual(Threshold.objects.filter(end_date=None).count(), 2)
        self.assertEqual(t2.end_date, None)
        self.assertEqual(Threshold.objects.get(pk=1).end_date, date.today())
