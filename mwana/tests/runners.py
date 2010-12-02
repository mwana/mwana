# vim: ai ts=4 sts=4 et sw=4
import logging

from test_extensions.testrunners.xmloutput import XMLTestSuiteRunner

logger = logging.getLogger('mwana.tests.runners')

class NoTeardownXMLTestRunner(XMLTestSuiteRunner):
    """
    Run the tests using the XML test suite runner, but down't try to teardown
    the DB.  For use with RapidSMS, when the test suite hangs trying to
    tear down the database at the end of the test run.
    """
    def teardown_databases(self, old_config, **kwargs):
        logger.info('skipping teardown_databases')
