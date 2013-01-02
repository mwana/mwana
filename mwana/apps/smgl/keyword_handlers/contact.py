import logging

from datetime import datetime, timedelta

from mwana.apps.smgl import const
from mwana.apps.smgl.decorators import registration_required, is_active
from mwana.apps.smgl.utils import (get_value_from_form, send_msg,
        get_session_message, respond_to_session)

logger = logging.getLogger(__name__)


@registration_required
@is_active
def leave(session, xform, router):
    """
    Handler for LEAVE keyword (Used to deactivate the user).

    Format:
    LEAVE NOW
    """
    logger.debug('Handling the LEAVE keyword form')
    connection = session.connection
    get_session_message(session)

    if not connection.contact:
        return respond_to_session(router, session, const.NOT_REGISTERED_FOR_DATA_ASSOC,
                                  is_error=True, **{'name': connection.contact.name})

    when = get_value_from_form('when', xform)
    if when == 'now':
        connection.contact.is_active = False
        connection.contact.save()
        return respond_to_session(router, session, const.LEAVE_COMPLETE,
                                  **{'name': connection.contact.name})

@registration_required
@is_active
def make_active(session, xform, router):
    """
    Handler for IN keyword (Used to re-activate the user early).

    Format:
    IN NOW
    """
    logger.debug('Handling the IN keyword form')
    connection = session.connection
    get_session_message(session)

    if not connection.contact:
        send_msg(connection, const.NOT_REGISTERED_FOR_DATA_ASSOC, router,
                 name=connection.contact.name)
        get_session_message(session, direction='O')

        return True

    when = get_value_from_form('when', xform)
    if when == 'now':
        connection.contact.is_active = True
        connection.contact.return_date = None
        connection.contact.save()

        send_msg(connection, const.IN_COMPLETE, router,
                 name=connection.contact.name)
        get_session_message(session, direction='O')
        return True


@registration_required
@is_active
def out(session, xform, router):
    """
    Handler for OUT keyword (Used to temporarily deactivate the user).

    Format:
    OUT ##_of_days
    """
    logger.debug('Handling the OUT keyword form')
    connection = session.connection
    get_session_message(session)
    if not connection.contact:
        send_msg(connection, const.NOT_REGISTERED_FOR_DATA_ASSOC, router,
                 name=connection.contact.name)
        get_session_message(session, direction='O')
        return True

    days = int(get_value_from_form('days', xform))
    now = datetime.utcnow().date()
    return_date = now + timedelta(days=days)

    connection.contact.is_active = False
    connection.contact.return_date = return_date
    connection.contact.save()

    send_msg(connection, const.OUT_COMPLETE, router,
             name=connection.contact.name,
             date=return_date.strftime("%d %m %Y")
             )
    get_session_message(session, direction='O')
