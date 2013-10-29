import logging

from datetime import datetime, timedelta

from mwana.apps.smgl import const
from mwana.apps.smgl.decorators import registration_required, is_active
from mwana.apps.smgl.utils import (get_value_from_form, respond_to_session)

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
def make_active(session, xform, router):
    """
    Handler for IN keyword (Used to re-activate the user early).

    Format:
    IN NOW
    """
    logger.debug('Handling the IN keyword form')
    connection = session.connection

    if not connection.contact:
        return respond_to_session(router, session, const.NOT_REGISTERED_FOR_DATA_ASSOC,
                                  is_error=True)

    when = get_value_from_form('when', xform)
    if when == 'now':
        connection.contact.is_active = True
        connection.contact.return_date = None
        connection.contact.save()
        return respond_to_session(router, session, const.IN_COMPLETE,
                                  **{'name': connection.contact.name})

@registration_required        
def make_active_back(session, xform, router):
    """
    Handler for Back Keyword
    """
    
    logger.debug("Handling the BACK keyword form")
    connection = session.connection
    
    if not connection.contact:
        return respond_to_session(router, session, const.NOT_REGISTERED_FOR_DATA_ASSOC,
                                  is_error=True)
    
    connection.contact.is_active = True
    connection.contact.return_date = None
    connection.contact.save()
    return respond_to_session(router, session, const.IN_COMPLETE,
                                **{'name': connection.contact.name })

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
    if not connection.contact:
        return respond_to_session(router, session, const.NOT_REGISTERED_FOR_DATA_ASSOC,
                                  is_error=True)

    days = int(get_value_from_form('days', xform))
    now = datetime.utcnow().date()
    return_date = now + timedelta(days=days)

    connection.contact.is_active = False
    connection.contact.return_date = return_date
    connection.contact.save()

    return respond_to_session(router, session, const.OUT_COMPLETE, 
                              **{'name': connection.contact.name,
                                 'date': return_date.strftime("%d %m %Y")})
