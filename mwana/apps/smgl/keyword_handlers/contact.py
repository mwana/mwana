import logging

from mwana.apps.smgl import const
from mwana.apps.smgl.decorators import registration_required, is_active
from mwana.apps.smgl.utils import (get_value_from_form, send_msg,
        get_session_message)

logger = logging.getLogger(__name__)


@registration_required
@is_active
def leave(session, xform, router):
    """
    Handler for LEAVE keyword (Used to deactivate the user).

    Format:
    LEAVE NOW
    """
    import ipdb; ipdb.set_trace()
    logger.debug('Handling the LEAVE keyword form')
    connection = session.connection
    get_session_message(session)

    if not connection.contact:
        send_msg(connection, const.NOT_REGISTERED_FOR_DATA_ASSOC, router,
                 name=connection.contact.name)
        get_session_message(session, direction='O')

        return True

    when = get_value_from_form('when', xform)
    if when == 'now':
        connection.contact.is_active = False
        connection.contact.save()

        send_msg(connection, const.LEAVE_COMPLETE, router,
                 name=connection.contact.name)
        get_session_message(session, direction='O')
        return True
