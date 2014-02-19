# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.stock.models import StockTransaction
from mwana.apps.stock.models import Transaction
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
            rb     > join clinic kdh rupiah banda 1234
            tk     > join clinic kdh tizie kays 1000
            """

        self.runScript(script)
        
        self.stock = Stock.objects.create(abbr='DRG-123', code='DRG-123', name='My Drug')
        self.stock2 = Stock.objects.create(abbr='DRG-124', code='DRG-124', name='Sondashi Formula')
        self.assertEqual(Stock.objects.all().count(), 2)

    def tearDown(self):
        super(TestApp, self).tearDown()
        Contact.objects.all().delete()
        Threshold.objects.all().delete()

class TestThreshold(TestApp):
    # TODO add test for low level notifications to DHO
    
    def test_threshold_addition(self):
        self.assertEqual(Threshold.objects.count(), 0)
        
        acc = StockAccount()
        acc.location = self.central_clinic
        acc.stock = self.stock
        acc.save()
        self.assertEqual(StockAccount.objects.all().count(), 1)
        self.assertEqual(Threshold.objects.all().count(), 1)


        acc2 = StockAccount.objects.create(stock=self.stock, location=self.kdh)
        self.assertEqual(Threshold.objects.all().count(), 2)

        t = Threshold()
        t.level = 6
        t.account = acc
        t.start_date = date.today() - timedelta(days=5)

        t.save()

        self.assertEqual(Threshold.objects.all().count(), 3)
        self.assertEqual(Threshold.objects.filter(end_date=None).count(), 3)

        t2 = Threshold.objects.create(level=12, account=acc)
        self.assertEqual(Threshold.objects.filter(account=acc).count(), 3)
        self.assertEqual(Threshold.objects.filter(account=acc, end_date=None).count(), 1)
        control= Threshold.objects.create(level=2, account=acc2)
        self.assertEqual(Threshold.objects.all().count(), 5)
        self.assertEqual(Threshold.objects.exclude(end_date=None).count(), 3)
        self.assertEqual(Threshold.objects.filter(end_date=None).count(), 2)
#        self.assertEqual(Threshold.objects.filter(end_date=None).count(), 2, str(Threshold.objects.filter(end_date=None).count())+ "....\n".join(t.__unicode__() for t in Threshold.objects.all().order_by('id')))
        self.assertEqual(t2.end_date, None)
        self.assertEqual(Threshold.objects.get(pk=1).end_date, date.today())


class TestStockAtFacility(TestApp):

    def test_new_stock_invalid_msgs(self):
        self.assertEqual(StockAccount.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)

        script = """
            rb > New Stock Bad-Drug 17
            rb < Sorry, I don't know stock with code BAD-DRUG. Please check your spelling and try again. If you think this message is a mistake send HELP.
            rb > New Stock DRG-123 23t
            rb < Sorry, 23T is not a valid number. Enter only numbers for quantity.
            rb > New Stock DRG-123 23, DRG-123 3, DRG-124 24
            rb < Sorry, drug ID(s) DRG-123 appears more than once in your message
        """

        self.runScript(script)
        self.assertEqual(StockAccount.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_new_stock_default_response(self):
        self.assertEqual(StockAccount.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)

        script = """
            rb > New Stock
            rb < To add new stock, send NEW STOCK <drug-code1> <quantity1>, <drug-code2> <quantity2> e.g NEW STOCK DG99 100, DG80 15
            rb > New Stock
            rb < To add new stock, send NEW STOCK <drug-code1> <quantity1>, <drug-code2> <quantity2> e.g NEW STOCK DG99 100, DG80 15
            rb > New Stock 123
            rb < To add new stock, send NEW STOCK <drug-code1> <quantity1>, <drug-code2> <quantity2> e.g NEW STOCK DG99 100, DG80 15
            unknown > NEW STOCK DG99 100
            unknown < Sorry, you must be registered to add new stock. Reply with HELP if you need assistance.
            unknown > NEW STOCK 100
            unknown < Sorry, you must be registered to add new stock. Reply with HELP if you need assistance.
        """

        self.runScript(script)
        self.assertEqual(StockAccount.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_new_stock_addition(self):
        self.assertEqual(StockAccount.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)

        script = """
            rb > New Stock DRG-123 23
            rb < Thank you. New levels for the added stock are: 23 units of DRG-123. Cc: 000001
        """

        self.runScript(script)
        self.assertEqual(StockAccount.objects.count(), 1)
        self.assertEqual(Transaction.objects.count(), 1)


    def test_new_stock_addition_multiple(self):
        self.assertEqual(StockAccount.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)

        StockAccount.objects.create(stock=self.stock, location=self.kdh)
        StockAccount.objects.create(stock=self.stock2, location=self.kdh)

        script = """
            rb > New Stock DRG-123 10, DRG-124 20
            rb < Thank you. New levels for the added stock are: 10 units of DRG-123, 20 units of DRG-124. Cc: 000001
            rb > New Stock DRG-123 5, DRG-124 15
            rb < Thank you. New levels for the added stock are: 15 units of DRG-123, 35 units of DRG-124. Cc: 000002
        """

        self.runScript(script)
        self.assertEqual(StockAccount.objects.count(), 2)
        self.assertEqual(Transaction.objects.count(), 2)

    def test_dispensed_stock(self):
        self.assertEqual(StockAccount.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)

        acc1 = StockAccount.objects.create(stock=self.stock, location=self.kdh)
        acc1.amount=50
        acc1.save()

        script = """
            rb > DISP DRG-123 23
            rb < Thank you. New levels for the just dispensed stock are: 27 units of DRG-123. Cc: 000001
        """

        self.runScript(script)
        self.assertEqual(StockAccount.objects.count(), 1)
        self.assertEqual(StockAccount.objects.filter(amount=27).count(), 1)
        self.assertEqual(Transaction.objects.count(), 1)


class TestStockTransactionManagement(TestApp):

    def test_undoing_new_stock(self):
        self.assertEqual(StockAccount.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)
        self.assertEqual(StockTransaction.objects.count(), 0)

        StockAccount.objects.create(stock=self.stock, location=self.kdh)
        StockAccount.objects.create(stock=self.stock2, location=self.kdh)

        script = """
            rb > New Stock DRG-123 10, DRG-124 20
            rb < Thank you. New levels for the added stock are: 10 units of DRG-123, 20 units of DRG-124. Cc: 000001
            rb > New Stock DRG-123 5, DRG-124 15
            rb < Thank you. New levels for the added stock are: 15 units of DRG-123, 35 units of DRG-124. Cc: 000002
        """

        self.runScript(script)
        self.assertEqual(StockAccount.objects.count(), 2)
        self.assertEqual(StockAccount.objects.get(stock=self.stock).amount, 15)
        self.assertEqual(StockAccount.objects.get(stock=self.stock2).amount, 35)
        self.assertEqual(Transaction.objects.count(), 2)
        self.assertEqual(Transaction.objects.filter(status='c').count(), 2)
        self.assertEqual(StockTransaction.objects.count(), 4)

        script = """
            tk > Del 000001
            tk < Sorry, I don't think you did a stock transaction with Confirmation code 000001. If you think this message is a mistake reply with HELP
            rb > Del 000006
            rb < Sorry, I don't think you did a stock transaction with Confirmation code 000006. If you think this message is a mistake reply with HELP
            rb > Del 00001
            rb < Your transaction with code 000001 has been cancelled. New levels for the affected stock are: 5 units of DRG-123, 15 units of DRG-124.
            rb > Del 00001
            rb < Your transaction with code 000001 has already been cancelled.
        """

        self.runScript(script)
        
        self.assertEqual(Transaction.objects.filter(status='x').count(), 1)
        self.assertEqual(StockAccount.objects.get(stock=self.stock).amount, 5)
        self.assertEqual(StockAccount.objects.get(stock=self.stock2).amount, 15)

        script = """
            tk > Del 000002
            tk < Sorry, I don't think you did a stock transaction with Confirmation code 000002. If you think this message is a mistake reply with HELP
            rb > Del 2
            rb < Your transaction with code 000002 has been cancelled. New levels for the affected stock are: 0 units of DRG-123, 0 units of DRG-124.
            rb > Del 000002
            rb < Your transaction with code 000002 has already been cancelled.
        """

        self.runScript(script)
        
        
        self.assertEqual(Transaction.objects.filter(status='x').count(), 2)
        self.assertEqual(StockAccount.objects.get(stock=self.stock).amount, 0)
        self.assertEqual(StockAccount.objects.get(stock=self.stock2).amount, 0)