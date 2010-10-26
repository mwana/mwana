from django.conf import settings # import the settings file


def static_project_media(context):
    return {'PROJECT_LOGO_URL': 'rapidsms/images/'+settings.PROJECT_LOGO_URL}
