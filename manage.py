#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import sys, os
from django.core.management import execute_manager

"""
This is basically a clone of the rapidsms runner, but it lives here because 
we will do some automatic editing of the python path in order to avoid 
sym-linking all the various dependencies that come in as submodules through
this project.
"""

if __name__ == "__main__":

    project_root = os.path.abspath(os.path.dirname(__file__))
    local_apps_root = os.path.join(project_root, "apps")
    
    rapidsms_root = os.path.join(project_root, "submodules", "rapidsms")
    rapidsms_lib = os.path.join(rapidsms_root, "lib")
    django_settings_root = os.path.join(rapidsms_root, "submodules", "django-app-settings")
    
    for dir in [project_root, local_apps_root, rapidsms_lib, django_settings_root]:
        print "adding %s to path" % dir
        sys.path.insert(0, dir)

    import settings
    execute_manager(settings)
