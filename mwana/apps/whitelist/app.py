import rapidsms
import logging
import datetime

from rapidsms.conf import settings

from mwana.apps.whitelist.models import TrialPeriod

logger = logging.getLogger(__name__)

class App(rapidsms.App):

    response = "I'm sorry, the system is not currently active. Please try "\
               "again later."
    keywords = "tryout|try"
    hours = 4

    def handle(self, msg):
        keyword = msg.text.split()[0].lower()
        handled = False
        if keyword in [k.lower() for k in self.keywords.split("|")]:
            expire_date = datetime.datetime.now() +\
                          datetime.timedelta(hours=self.hours)
            TrialPeriod.objects.create(connection=msg.connection,
                                       start_date=datetime.datetime.now(),
                                       expire_date=expire_date)
            msg.respond("You have been granted a %s hour trial period to "
                        "test Results160 and RemindMi." % self.hours)
            handled = True
        elif not TrialPeriod.objects.filter(connection=msg.connection,
                              expire_date__gt=datetime.datetime.now()).count():
            logger.info('connection from %s DENIED (not whitelisted)' %
                        msg.connection)
            if hasattr(settings, 'WHITELIST_RESPONSE'):
                msg.respond(settings.WHITELIST_RESPONSE)
            else:
                msg.respond(self.response)
            handled = True
        else:
            logger.info('connection from %s ALLOWED (whitelisted)' %
                        msg.connection)
        return handled
