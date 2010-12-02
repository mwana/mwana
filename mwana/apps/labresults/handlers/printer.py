from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact, Connection, Backend

from mwana.apps.locations.models import Location
from mwana.apps.tlcprinters.messages import TLCOutgoingMessage

from mwana import const

# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that makemessages finds
# our text.
_ = lambda s: s

HELP_MSG = _('To add or remove a printer, send PRINTER ADD|REMOVE <location> <backend> <phone #>')

class PrinterHandler(KeywordHandler):
    '''
    '''

    keyword = 'printer'
    
    def help(self):
        # Because we want to process this with just an empty keyword, rather
        # than respond with a help message, just call the handle method from
        # here.
        self.handle('')

    def handle(self, text):
        if not self.msg.contact or not self.msg.contact.is_help_admin:
            self.respond('You must be a registered help admin to add or '
                         'remove printers.')
            return
        words = text.split()
        if len(words) != 4:
            self.respond(HELP_MSG)
            return
        action, location_slug, backend_name, phone = words
        action = action.lower()
        if action not in ('add', 'remove'):
            self.respond(HELP_MSG)
            return
        try:
            location = Location.objects.get(slug=location_slug)
        except Location.DoesNotExist:
            self.respond('Location ID %s is not known.' % location_slug)
            return
        try:
            backend = Backend.objects.get(name=backend_name)
        except Backend.DoesNotExist:
            self.respond('Backend name %s is not known.' % backend_name)
            return
        # prepend the country code if the shorthand was given
        if phone.startswith('0') and hasattr(settings, 'COUNTRY_CODE'):
            phone = settings.COUNTRY_CODE + phone[1:]
        if action == 'add':
            contact = Contact.objects.create(name='Printer in %s' % location.name,
                                             location=location)
            conn = Connection.objects.create(identity=phone, backend=backend,
                                             contact=contact)
            contact.types.add(const.get_dbs_printer_type())
            conf_msg = TLCOutgoingMessage(conn, 'You have successfully '
                                          'registered this printer at '
                                          '%(location)s. You will receive '
                                          'results as soon as they are '
                                          'available.', location=location.name)
            conf_msg.send()
            self.respond('Printer added successfully.')
        elif action == 'remove':
            try:
                conn = Connection.objects.get(identity=phone, backend=backend,
                                              contact__types=const.get_dbs_printer_type(),
                                              contact__location=location,
                                              contact__is_active=True)
            except Connection.DoesNotExist:
                self.respond('No active printer found with that backend and phone number at that location.')
                return
            contact = conn.contact
            contact.is_active = False
            contact.save()
            conn.contact = None
            conn.save()
            conf_msg = TLCOutgoingMessage(conn, 'This printer has been '
                                          'deregistered from %(location)s. You '
                                          'will no longer receive results.',
                                          location=location.name)
            conf_msg.send()
            self.respond('Printer removed successfully.')
