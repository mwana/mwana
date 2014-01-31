import os, sys
import site
site.addsitedir('~/.virtualenvs/mwana/lib/python2.7/site-packages/')

sys.path.append('/var/www/mubumi/mwana')
sys.path.append('/var/www/mubumi/mwana/mwana')

SUBMODULE_NAMES = [
    'rapidsms-smsforms',
    'touchforms',
    "rapidsms-smscouchforms",
    "couchforms",
    "couchexport",
    "couchlog",
    "django-soil",
    "django-scheduler",
    "rapidsms-dupe-checker"
]
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
os.environ['DJANGO_SETTINGS_MODULE'] = 'mwana.localsettings'

import djcelery
djcelery.setup_loader()

import  django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

