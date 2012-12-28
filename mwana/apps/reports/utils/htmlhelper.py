# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.locations.models import Location
from mwana.apps.contactsplus.models import ContactType
from datetime import date

from mwana.apps.reports.webreports.models import ReportingGroup

def get_groups_name(id):
    try:
        return ReportingGroup.objects.get(pk=id)
    except:
        return "All"

def text_date(text):
    delimiters = ('-', '/')
    for delim in delimiters:
        text = text.replace(delim, ' ')
    a, b, c = text.split()
    if len(a) == 4:
        return date(int(a), int(b), int(c))
    else:
        return date(int(c), int(b), int(a))


def get_contacttype_dropdown_html(id, selected_worker_type=None):
    code ='<select name="%s" size="1">\n'%id
    code +='<option value="All">All</option>\n'
    for type in ContactType.objects.exclude(name__in=["Patient", "DBS Printer"]):
        if type.slug == selected_worker_type:
            code = code + '<option selected value="%s">%s</option>\n'%(type.slug,type.name)
        else:
            code = code + '<option value="%s">%s</option>\n'%(type.slug,type.name)

    code = code +'</select>'
    return code

def get_contacttypes(slug):
    if slug is None:
        return ContactType.objects.exclude(name__in=["Patient", "DBS Printer"])
    else:
        return ContactType.objects.filter(slug=slug).exclude(name__in=["Patient", "DBS Printer"])

def get_facilities_dropdown_html(id, facilities, selected_facility, get_only_select=False):
    if not facilities:
        return '<select name="%s" size="1"></select>\n'%id
    code ='<select name="%s"" onchange="fire%sChange()" id="%s" class="drop-down" size="1">\n' % (id, id, id)
    if selected_facility and get_only_select:
        pass
    else:
        code +='<option value="All">All</option>\n'
    for fac in facilities:
        if fac.slug == selected_facility:
            code = code + '<option selected value="%s">%s</option>\n'%(fac.slug,fac.name)
        elif get_only_select:
            pass
        else:
            code = code + '<option value="%s">%s</option>\n'%(fac.slug,fac.name)

    code = code +'</select>'
    return code

def get_facilities_dropdown_htmlb(id, facilities, selected_facility):
    code ='<select name="%s" size="1">\n'%id
    for fac in facilities:
        if fac.slug == selected_facility:
            code = code + '<option selected value="%s">%s</option>\n'%(fac.slug,fac.name)
        else:
            code = code + '<option value="%s">%s</option>\n'%(fac.slug,fac.name)

    code = code +'</select>'
    return code

def get_groups_dropdown_html(id, selected_group):
    #TODO: move this implemention to templates
    code ='<select name="%s" id="%s" class="drop-down" size="1">\n'%(id, id)
    code +='<option value="All">All</option>\n'
    for group in ReportingGroup.objects.all():
        if str(group.id) == selected_group:
            code = code + '<option selected value="%s">%s</option>\n'%(group.id,group.name)
        else:
            code = code + '<option value="%s">%s</option>\n'%(group.id,group.name)

    code = code +'</select>'
    return code

def read_request(request,param):
    try:
        value = request.REQUEST[param]
        if value =='All':
            value = None
    except:
        value = None
    return value

def try_format(date):
    try:
        return date.strftime("%Y-%m-%d")
    except:
        return date


def get_int(val):
    return int(val) if str(val).isdigit() else None

def get_default_int(val):
    return int(val) if str(val).isdigit() else 0

def get_groups_name(id):
    try:
        return ReportingGroup.objects.get(pk=id)
    except:
        return "All"

def get_facility_name(slug):
    try:
        return Location.objects.get(slug=slug)
    except:
        return "All"

def get_next_navigation(text):
    try:
        return {"Next":1,"Previous":-1}[text]
    except:
        return 0

def get_default_int(val):
    return int(val) if str(val).isdigit() else 0

def get_distinct_parents(locations, type_slugs=None):
    if not locations:
        return None
    parents = []
    for location in locations:
        if not type_slugs or (location.parent and location.parent.type.slug in type_slugs):
            parents.append(location.parent)

    return list(set(parents))

def get_rpt_provinces(user):
    return get_distinct_parents(get_rpt_districts(user))

def get_rpt_districts(user):

    return get_distinct_parents(Location.objects.filter(groupfacilitymapping__group__groupusermapping__user=user))

def get_rpt_facilities(user):
    return Location.objects.filter(groupfacilitymapping__group__groupusermapping__user=user)
