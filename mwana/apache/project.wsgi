import os
import os.path
import sys

#Calculate the project path based on the location of the WSGI script.
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(PROJECT_ROOT))

SHOW_UPGRADE_MESSAGE = False
ADMIN_IPS = ('127.0.0.1',)
UPGRADE_FILE = os.path.join(PROJECT_ROOT, 'media', 'html', 'upgrade.html')
ERROR_FILE = os.path.join(PROJECT_ROOT, 'media', 'html', 'server_error.html')

os.environ['DJANGO_SETTINGS_MODULE'] = 'mwana.localsettings'
os.environ['PYTHON_EGG_CACHE'] = '/var/data/.python_eggs'

try:
    rapidsms_root = os.path.join(PROJECT_ROOT, "submodules", "rapidsms")
    rapidsms_lib = os.path.join(rapidsms_root, "lib")
    django_settings_root = os.path.join(rapidsms_root, "submodules", "django-app-settings")
    django_tables_root = os.path.join(rapidsms_root, "submodules", "django-tables")
    
    for dir in [PROJECT_ROOT, rapidsms_lib, django_settings_root, django_tables_root]:
        sys.path.insert(0, dir)
    
    from mwana.logconfig import init_django_logging
    init_django_logging()
    import django.core.handlers.wsgi
    django_app = django.core.handlers.wsgi.WSGIHandler()
except:
    import traceback
    traceback.print_exc(file=sys.stderr)
    django_app = None

def static_response(environ, start_response, status, file, default_message=''):
    response_headers = [('Retry-After', '120')] # Retry-After: <seconds>
    if os.path.exists(file):
        response_headers.append(('Content-type','text/html'))
        response = open(file).read()
    else:
        response_headers.append(('Content-type','text/plain'))
        response = default_message
    start_response(status, response_headers)
    return [response]

def server_error(environ, start_response):
    status = '500 Internal Server Error'
    msg = 'Internal Server Error...please retry in a few minutes.'
    return static_response(environ, start_response, status, ERROR_FILE, msg)

def upgrade_in_progress(environ, start_response):
    if environ['REMOTE_ADDR'] in ADMIN_IPS and django_app:
        return django_app(environ, start_response)
    
    if environ['REQUEST_METHOD'] == 'GET':
        status = '503 Service Unavailable'
    else:
        status = '405 Method Not Allowed'
    
    msg = 'Upgrade in progress...please retry in a few minutes.'
    return static_response(environ, start_response, status, UPGRADE_FILE, msg)
    
class LoggingMiddleware(object):
    def __init__(self, application):
        self.__application = application

    def __call__(self, environ, start_response):
        try:
            return self.__application(environ, start_response)
        except:
            import traceback
            traceback.print_exc(file=sys.stderr)
            return server_error(environ, start_response)

if SHOW_UPGRADE_MESSAGE:
    application = upgrade_in_progress
elif not django_app:
    application = server_error
else:
    application = LoggingMiddleware(django_app)
