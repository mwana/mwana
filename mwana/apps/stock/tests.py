# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.stock.models import LowStockLevelNotification
from mwana.apps.stock.models import Supported
from mwana.apps.stock.models import StockTransaction
from mwana.apps.stock.models import Transaction
from mwana.apps.stock import tasks
from datetime import timedelta
from mwana.apps.stock.models import Stock
from mwana.apps.stock.models import StockAccount
from datetime import date
import time

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
        
        self.luapula = Location.objects.create(name="Luapula",
                                          slug="400000", type=prv)
        
        self.mansa = Location.objects.create(name="Mansa",
                                        slug="403000", type=dst,
                                        parent=self.luapula)
        self.nchelenge = Location.objects.create(name="Nchelenge",
                                        slug="406000", type=dst,
                                        parent=self.luapula)
        self.central_clinic = Location.objects.create(name="Central Clinic",
                                                 slug="403012", type=ctr,
                                                 parent=self.mansa)
        self.kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr,
                                                 parent=self.mansa)
        script = """            
            rb     > join clinic kdh rupiah banda 1234
            tk     > join clinic kdh tizie kays 1000
            dho     > join dho 403000 Mr kays 1002
            pho     > join pho 400000 Mr Peters 1002
            """

        self.runScript(script)
        self.assertEqual(4, Contact.objects.count())
        
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
        acc2 = StockAccount.objects.create(stock=self.stock2, location=self.kdh)
        acc1.amount = 50
        acc1.save()
        acc2.amount = 44
        acc2.save()

        script = """
            rb > DISP DRG-123 23, Drg-124 4
            rb < Thank you. New levels for the just dispensed stock are: 27 units of DRG-123, 40 units of DRG-124. Cc: 000001
            rb > DISP DRG-123 23, Drg-124 60
            rb < Sorry, you cannot dispense 60 units of DRG-124 from your balance of 40. If you think this message is a mistake reply with HELP
            rb > DISP DRG-123 30, Drg-124 6
            rb < Sorry, you cannot dispense 30 units of DRG-123 from your balance of 27. If you think this message is a mistake reply with HELP
        """

        self.runScript(script)
        self.assertEqual(StockAccount.objects.count(), 2)
        self.assertEqual(StockAccount.objects.filter(amount=27).count(), 1)
        self.assertEqual(Transaction.objects.count(), 3)
        self.assertEqual(Transaction.objects.filter(status='x').count(), 2)
        self.assertEqual(Transaction.objects.filter(status='c').count(), 1)


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


class TestSendStockBelowThresholdNotification(TestApp):

    def test_district_notification(self):
        self.assertEqual(Threshold.objects.count(), 0)

        acc = StockAccount()
        acc.location = self.central_clinic
        acc.stock = self.stock
        acc.amount = 23
        acc.save()
        self.assertEqual(StockAccount.objects.all().count(), 1)
        self.assertEqual(Threshold.objects.all().count(), 1)
        Supported.objects.create(district=self.mansa, supported=True)
        self.assertEqual(Supported.objects.all().count(), 1)


        time.sleep(0.1)
        self.startRouter()
        tasks.send_stock_below_threshold_notification(self.router)
        msgs = self.receiveAllMessages()
        self.stopRouter()

        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].text, 'Hi. Following stock are below thresholds: Central Clinic-DRG-123=23')
        self.assertEqual(msgs[0].contact.name, 'Mr Kays')

        StockAccount.objects.create(location = self.kdh, stock = self.stock2, amount = 10)
        acc.amount = 30
        acc.save()
        self.assertEqual(StockAccount.objects.all().count(), 2)
        self.assertEqual(Threshold.objects.all().count(), 2)

        time.sleep(0.1)
        self.startRouter()
        tasks.send_stock_below_threshold_notification(self.router)
        msgs = self.receiveAllMessages()
        self.stopRouter()

        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].text, 'Hi. Following stock are below thresholds: Kafue District Hospital-DRG-124=10')
        self.assertEqual(msgs[0].contact.name, 'Mr Kays')


        acc.amount = 7
        acc.save()
        self.assertEqual(StockAccount.objects.all().count(), 2)
        self.assertEqual(Threshold.objects.all().count(), 2)

        time.sleep(0.1)
        self.startRouter()
        tasks.send_stock_below_threshold_notification(self.router)
        msgs = self.receiveAllMessages()
        self.stopRouter()

        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].text, 'Hi. Following stock are below thresholds: Central Clinic-DRG-123=7')
        self.assertEqual(msgs[0].contact.name, 'Mr Kays')
        time.sleep(0.1)

        # Don't send same messages again
        self.startRouter()
        tasks.send_stock_below_threshold_notification(self.router)
        msgs = self.receiveAllMessages()
        self.stopRouter()

        self.assertEqual(0, len(msgs))


        for sa in StockAccount.objects.all():
            sa.amount = 4
            sa.save()
       
        self.assertEqual(StockAccount.objects.all().count(), 2)
        self.assertEqual(Threshold.objects.all().count(), 2)

        time.sleep(0.1)
        self.startRouter()
        tasks.send_stock_below_threshold_notification(self.router)
        msgs = self.receiveAllMessages()
        self.stopRouter()

        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].text, 'Hi. Following stock are below thresholds: Kafue District Hospital-DRG-124=4*** Central Clinic-DRG-123=4')
        self.assertEqual(msgs[0].contact.name, 'Mr Kays')
        time.sleep(0.1)
