#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.conf import settings
import rapidsms
import logging

logger = logging.getLogger(__name__)

class App(rapidsms.App):

    def handle(self, msg):
        if settings.DEFAULT_RESPONSE:
            logger.info('sending DEFAULT_RESPONSE to %s' % msg.connection)
            msg.respond(settings.DEFAULT_RESPONSE,
                        project_name=settings.PROJECT_NAME)
            return True
