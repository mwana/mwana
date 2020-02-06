# vim: ai ts=4 sts=4 et sw=4
"""
One off task to create RapidSMS contacts for one backend based on another.
- for each active clinic contact on connection with backend1 (that's down)
-     create a near duplicate contact but with connection on backend2
-     send the contact a message that a new contact has been created
"""

from mwana.apps.monitor.models import EmergencyContact
from django.contrib.auth.models import User
from mwana.apps.websmssender.models import StagedMessage
from django.core.management.base import CommandError
from django.core.management.base import LabelCommand
from mwana.const import get_clinic_worker_type, get_hub_worker_type, get_cba_type, get_district_worker_type,\
    get_lab_worker_type, get_province_worker_type
from rapidsms.models import Backend, Contact, Connection
import logging


logger = logging.getLogger(__name__)


class Command(LabelCommand):
    help = """
        One off task to create RapidSMS contacts for one backend based on another.
        - for each active clinic contact on connection with backend1 (that's down)
        -     create a near duplicate contact but with connection on backend2
        -     send the contact a message that a new contact has been created
        """
    args = "<from_backend> <to_backend>"
    label = 'Backend_From Backend_To smsc-number'

    def handle(self, *args, **options):
        if len(args) < 3:
            raise CommandError('Please specify %s' % self.label)
        create_emergency_contacts(args[0], args[1], args[2])

    def __del__(self):
        pass


def create_emergency_contacts(from_backend, to_backend, usual_number='short code'):
    """
        One off task to create RapidSMS contacts for one backend based on another.
        - for each active clinic contact on connection with backend1 (that's down)
        -     create a near duplicate contact but with connection on backend2
        -     send the contact a message that a new contact has been created
        """

    backends = Backend.objects.filter(name=from_backend)
    if not backends:
        print("backend with name %s does not exist." % from_backend)
        return

    source_backend = backends[0]

    backends = Backend.objects.filter(name=to_backend)
    if not backends:
        print("backend with name %s does not exist." % to_backend)
        return

    target_backend = backends[0]
    choice = raw_input("Are you sure you want to create contacts on %s backend based on %s backend? Y/N  " % (
        target_backend, source_backend ))
    if choice.lower() != 'y':
        print "Process termination here."
        return

    for contact in Contact.active.filter(types__in=[get_clinic_worker_type(),  get_hub_worker_type(),  get_cba_type(),  get_district_worker_type(),
                                                    get_lab_worker_type(),  get_province_worker_type()], connection__backend=source_backend):
        identity = contact.default_connection.identity
        conn, created = Connection.objects.get_or_create(backend=target_backend, identity=identity)
        if not created and conn.contact:
            print("Connection with backend %s and identity %s already exists with an active contact" % (target_backend.name, identity))
            continue

        # clever way to create 'duplicate' record but with different primary key
        contact.pk = None
        contact.save()

        conn.contact = contact
        conn.save()

        contact1 = Contact.active.get(connection__backend=source_backend, connection__identity=identity)
        contact2 = Contact.active.get(connection__backend=target_backend, connection__identity=identity)
        for type in contact1.types.all():
            contact2.types.add(type)
        contact2.save()
        # @type contact1 Contact
        contact1.is_active = False
        contact1.save()
        
        EmergencyContact.objects.get_or_create(usual_contact=contact1, emergency_contact=contact2)

        text = "We are very sorry %s. %s is still down. Your PIN code is the same. From Mwana/Results160 Support" % (contact2.name[:30], usual_number)
        user = None
        user = User.objects.get(username="You can't see me here")

        StagedMessage.objects.create(connection=contact2.default_connection, text=text, user=user)
        
        print "We now have", contact1, contact1.default_connection, "and ", contact2, contact2.default_connection



