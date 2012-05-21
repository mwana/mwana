#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import sys, os
from os.path import exists, join
from django.core.management import execute_manager

# use a default settings module if none was specified on the command line
DEFAULT_SETTINGS = 'mwana.localsettings'
DEFAULT_TEST_SETTINGS = 'mwana.test_localsettings'
settings_specified = any([arg.startswith('--settings=') for arg in sys.argv])
if not settings_specified and len(sys.argv) >= 2:
    settings = DEFAULT_SETTINGS
    print "NOTICE: using default settings module '%s'" % settings    
    sys.argv.append('--settings=%s' % settings)


#just add the name of the submodule you want to include here.
#Make sure it's in the repo_root/submodules folder!
SUBMODULE_NAMES = [
    'rapidsms-smsforms',
    'touchforms',
    "rapidsms-smscouchforms",
    "couchforms",
    "couchexport",
    "couchlog",
    "django-soil",
]
if __name__ == "__main__":
    # all imports should begin with the full Python package ('mwana.'):
    project_root = os.path.abspath(os.path.dirname(__file__))
    if project_root in sys.path:
        sys.path.remove(project_root)
    sys.path.insert(0, os.path.dirname(project_root))


    #add submodules
    submodule_root = os.path.join(project_root, '..', 'submodules')
    for submodule in SUBMODULE_NAMES:
        submodule_path = os.path.join(submodule_root, submodule)
        sys.path.append(submodule_path)

    from mwana import settings_project    
    if len(sys.argv) > 1 and sys.argv[1] == 'test' and settings_project.ON_LIVE_SERVER:
        print "___"*20
        print '\nPlease set "ON_LIVE_SERVER" to False in settings_project\n'
        print "___"*20
        sys.exit()
    # the argument '--mwana-apps' automatically tests all mwana apps specified
    # in the project-level settings file (settings_project.py) that include
    # a file named 'tests.py'
    elif len(sys.argv) > 1 and sys.argv[1] == 'test' and '--mwana-apps' in sys.argv:
        sys.argv.remove('--mwana-apps')
        apps = settings_project.INSTALLED_APPS
        apps = filter(lambda a: a.startswith('mwana.apps'), apps)
        apps = [a.split('.')[-1] for a in apps]
        apps = filter(lambda a: exists(join('apps', a, 'tests.py')), apps)
        apps.sort()
        print 'NOTICE: running tests for the following mwana apps: %s' %\
              ', '.join(apps)
        sys.argv.extend(apps)
    # Use test_database for tests instead of regular database settings
    elif len(sys.argv) > 1 and sys.argv[1] == 'test':
        import mwana.localsettings as localsettings
        test_db = getattr(localsettings, 'TEST_DATABASES', localsettings.DATABASES)
        localsettings.DATABASES = test_db
    execute_manager(settings_project)
