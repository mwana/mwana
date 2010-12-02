# vim: ai ts=4 sts=4 et sw=4
from django.conf import settings # import the settings file


def static_project_media(context):
    return {'PROJECT_LOGO_URL': 'rapidsms/images/'+settings.PROJECT_LOGO_URL}
