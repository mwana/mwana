from mwana.apps.reports.webreports.models import UserPreference
# vim: ai ts=4 sts=4 et sw=4

NAME_REPORTS_SHOW_EXPORT_TO_CSV_INTRO = "NAME_REPORTS_SHOW_EXPORT_TO_CSV_INTRO"
VALUE_REPORTS_SHOW_EXPORT_TO_CSV_INTRO_YES = 1
VALUE_REPORTS_SHOW_EXPORT_TO_CSV_INTRO_NO = 0


def preference_exists(user, preference_name, preference_value):
    return UserPreference.objects.filter(user=user, preference_name=preference_name, preference_value=preference_value).exists()


def save_preference(user, preference_name, preference_value, extra_preference_value=None):
    pref, created = UserPreference.objects.get_or_create(user=user, preference_name=preference_name)
    pref.preference_value = preference_value
    
    if extra_preference_value:
        pref.extra_preference_value = extra_preference_value

    pref.save()
    return pref
