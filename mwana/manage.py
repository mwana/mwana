#!/usr/bin/env python

import sys, os
from django.core.management import execute_manager

# use a default settings module if none was specified on the command line
DEFAULT_SETTINGS = 'mwana.localsettings'
settings_specified = any([arg.startswith('--settings=') for arg in sys.argv])
if not settings_specified and len(sys.argv) >= 2:
    print "NOTICE: using default settings module '%s'" % DEFAULT_SETTINGS
    sys.argv.append('--settings=%s' % DEFAULT_SETTINGS)

"""
This is basically a clone of the rapidsms runner, but it lives here because 
we will do some automatic editing of the python path in order to avoid 
sym-linking all the various dependencies that come in as submodules through
this project.
"""

if __name__ == "__main__":
    # remove '.' from sys.path (anything in this package should be referenced
    # with the 'mwana.' prefix)
    sys.path.pop(0)

    project_root = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    
    rapidsms_root = os.path.join(project_root, "mwana", "submodules", "rapidsms")
    rapidsms_lib = os.path.join(rapidsms_root, "lib")
    django_settings_root = os.path.join(rapidsms_root, "submodules", "django-app-settings")
    django_tables_root = os.path.join(rapidsms_root, "submodules", "django-tables")
    
    for dir in [django_settings_root, django_tables_root, rapidsms_lib, project_root]:
        sys.path.insert(0, dir)
    
    from mwana import settings
    execute_manager(settings)
