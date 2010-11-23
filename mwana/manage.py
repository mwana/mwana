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
    if sys.argv[1] == 'test':
        settings = DEFAULT_TEST_SETTINGS
    else:
        settings = DEFAULT_SETTINGS
    print "NOTICE: using default settings module '%s'" % settings    
    sys.argv.append('--settings=%s' % settings)


if __name__ == "__main__":
    # all imports should begin with the full Python package ('mwana.'):
    project_root = os.path.abspath(os.path.dirname(__file__))
    if project_root in sys.path:
        sys.path.remove(project_root)
    sys.path.insert(0, os.path.dirname(project_root))

    from mwana import settings_project
    # the argument '--mwana-apps' automatically tests all mwana apps specified
    # in the project-level settings file (settings_project.py) that include
    # a file named 'tests.py'
    if sys.argv[1] == 'test' and '--mwana-apps' in sys.argv:
        sys.argv.remove('--mwana-apps')
        apps = settings_project.INSTALLED_APPS
        apps = filter(lambda a: a.startswith('mwana.apps'), apps)
        apps = [a.split('.')[-1] for a in apps]
        apps = filter(lambda a: exists(join('apps', a, 'tests.py')), apps)
        apps.sort()
        print 'NOTICE: running tests for the following mwana apps: %s' %\
              ', '.join(apps)
        sys.argv.extend(apps)
    execute_manager(settings_project)
