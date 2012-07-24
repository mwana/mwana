from rapidsms.messages.outgoing import OutgoingMessage
from mwana.apps.smgl import const
import functools

class registration_required(object):
    """
    Wrapper for a keyword handler to require registration
    """
    # see: http://wiki.python.org/moin/PythonDecoratorLibrary
    
    def __init__(self, func):
        self.func = func
        
    
    def __call__(self, session, xform, router):
        if not session.connection.contact:
            # TODO: should we set something in the form here?
            router.outgoing(OutgoingMessage(session.connection, 
                                            const.NOT_REGISTERED))
            return True
        else:
            return self.func(session, xform, router)
    
    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__
    
    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)
