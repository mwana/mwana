from rapidsms.messages.outgoing import OutgoingMessage
from mwana.apps.smgl import const
import functools
from mwana.apps.smgl.utils import respond_to_session

class registration_required(object):
    """
    Wrapper for a keyword handler to require registration
    """
    # see: http://wiki.python.org/moin/PythonDecoratorLibrary

    def __init__(self, func):
        self.func = func

    def __call__(self, session, xform, router):
        if not session.connection.contact:
            return respond_to_session(router, session, const.NOT_REGISTERED,
                                      is_error=True)
        else:
            return self.func(session, xform, router)

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)


class is_active(object):
    """
    Wrapper for a keyword handler to require the contact being active or
    inactive with a return date
    """
    # see: http://wiki.python.org/moin/PythonDecoratorLibrary

    def __init__(self, func):
        self.func = func

    def __call__(self, session, xform, router):
        contact = session.connection.contact
        if not contact.is_active and not contact.return_date:
            # TODO: should we set something in the form here?
            router.outgoing(OutgoingMessage(session.connection,
                                            const.DEACTIVATED))
            return True
        elif not contact.is_active:
            # Reactivate the contact
            contact.is_active = True
            contact.return_date = None
            contact.save()
        return self.func(session, xform, router)

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)
