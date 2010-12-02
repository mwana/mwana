# vim: ai ts=4 sts=4 et sw=4
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module


def get_class(import_path):
    """
    Imports the class described by import_path, where
    import_path is the full Python path to the class.
    """
    try:
        dot = import_path.rindex('.')
    except ValueError:
        raise ImproperlyConfigured("%s isn't a Python path." % import_path)
    module, classname = import_path[:dot], import_path[dot + 1:]
    try:
        mod = import_module(module)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing module %s: "%s"' %
                                   (module, e))
    try:
        return getattr(mod, classname)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" '
                                   'class.' % (module, classname))
