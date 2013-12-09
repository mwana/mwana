# vim: ai ts=4 sts=4 et sw=4
from datetime import date

from django.contrib.csrf.middleware import csrf_response_exempt
from django.contrib.csrf.middleware import csrf_view_exempt
from django.shortcuts import render_to_response
from django.template import RequestContext
from mwana.apps.issuetracking.issuehelper import IssueHelper
from mwana.apps.reports.webreports.models import ReportingGroup
from mwana.apps.training.forms import TrainedForm
from mwana.apps.training.models import Trained
from mwana.const import get_cba_type
from mwana.const import get_clinic_worker_type
from mwana.const import get_district_worker_type
from mwana.const import get_hub_worker_type
from mwana.const import get_province_worker_type





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
        return {"Next":1, "Previous":-1}[text]
    except:
        return 0

def text_date(text):
    delimiters = ('-', '/')
    for delim in delimiters:
        text = text.replace(delim, ' ')
    a, b, c = text.split()
    if len(a) == 4:
        return date(int(a), int(b), int(c))
    else:
        return date(int(c), int(b), int(a))



def get_groups_dropdown_html(id, selected_group):
    #TODO: move this implemention to templates
    code = '<select name="%s" id="%s" class="drop-down" size="1">\n' % (id, id)
    code += '<option value="All">All</option>\n'
    for group in ReportingGroup.objects.all():
        if str(group.id) == selected_group:
            code = code + '<option selected value="%s">%s</option>\n' % (group.id, group.name)
        else:
            code = code + '<option value="%s">%s</option>\n' % (group.id, group.name)

    code = code + '</select>'
    return code

def read_request(request, param):
    try:
        value = request.REQUEST[param].strip()
        if value == 'All':
            value = None
    except:
        value = None
    return value

def try_format(date):
    try:
        return date.strftime("%Y-%m-%d")
    except:
        return date

def get_admin_email_address():
    from djappsettings import settings
    try:
        return settings.ADMINS[0][1]
    except:
        return "Admin's email address"


def get_trained_data(type):
    trained = Trained.objects.all()
    trained_cbas = trained.filter(type=type)

    from collections import defaultdict
    dict = defaultdict(list)
    total = 0
    for item in trained_cbas:
        key = item.trained_by.name if item.trained_by else ""
        if not key:
            key = "Unclear"
        elif "DHO" in key.upper() or "PHO" in key.upper() or "MOH" in key.upper():
            key = "MoH"
        dict[key].append(1)
        total = total + 1

    trainer_labels = []
    trainer_values = []
    for a in dict:
        trainer_labels.append(a)
        trainer_values.append(len(dict[a]))

    return "[%s]" % ','.join("'%s'" % i for i in trainer_labels), trainer_values, total

@csrf_response_exempt
@csrf_view_exempt
def trained(request):
    name_dir = phone_dir = email_dir = location_dir = type_dir = trained_by_dir = date_dir = additional_text_dir = "asc"

    sort = request.REQUEST.get("o", "date")
    order = request.REQUEST.get("ot", "ass")
    direction = {'asc':'', 'desc':'-'}.get(order, '')
    
    if sort == 'name': name_dir = {'asc':'desc', 'desc':'asc'}.get(order, 'asc')
    elif sort == 'phone': phone_dir = {'asc':'desc', 'desc':'asc'}.get(order, 'asc')
    elif sort == 'email': email_dir = {'asc':'desc', 'desc':'asc'}.get(order, 'asc')
    elif sort == 'location': location_dir = {'asc':'desc', 'desc':'asc'}.get(order, 'asc')
    elif sort == 'type': type_dir = {'asc':'desc', 'desc':'asc'}.get(order, 'asc')
    elif sort == 'trained_by': trained_by_dir = {'asc':'desc', 'desc':'asc'}.get(order, 'asc')
    elif sort == 'date': date_dir = {'asc':'desc', 'desc':'asc'}.get(order, 'asc')
    elif sort == 'additional_text': additional_text = {'asc':'desc', 'desc':'asc'}.get(order, 'asc')

    navigation = read_request(request, "navigate")
    page = read_request(request, "page")
    


    page = get_default_int(page)
    page = page + get_next_navigation(navigation)
    confirm_message = ""

    form = TrainedForm() # An unbound form
    if request.method == 'POST': # If the form has been submitted...
        form = TrainedForm(request.POST) # A form bound to the POST data
        if form.is_valid():
            name = form.cleaned_data['name']
            phone = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            trained_by = form.cleaned_data['trained_by']
            type = form.cleaned_data['type']
            date = form.cleaned_data['date']
            location = form.cleaned_data['location']
            additional_text = form.cleaned_data['additional_text']
            if not email:email = None
            if not additional_text:additional_text = None


            model = Trained(name=name, phone=phone, email=email,
                            trained_by=trained_by, type=type, date=date, location=location,
                            additional_text=additional_text)


            model.save()


            form = TrainedForm() # An unbound form
            confirm_message = "%s has been succesfully saved" % model




    issueHelper = IssueHelper()

    (query_set, num_pages, number, has_next, has_previous), max_per_page = issueHelper.get_trained_people("%s%s" % (direction, sort), page)

    offset = max_per_page * (number - 1)
 
    
    cba_trainer_labels, cba_trainer_values, cba_total = get_trained_data(get_cba_type())
    dho_trainer_labels, dho_trainer_values, dho_total = get_trained_data(get_district_worker_type())
    pho_trainer_labels, pho_trainer_values, pho_total = get_trained_data(get_province_worker_type())
    hub_trainer_labels, hub_trainer_values, hub_total = get_trained_data(get_hub_worker_type())
    clinic_trainer_labels, clinic_trainer_values, clinic_total = get_trained_data(get_clinic_worker_type())

    return render_to_response('training/trained.html',
                              {
                              'form': form,
                              'model': 'Trained people',
                              'query_set': query_set,
                              'confirm_message': confirm_message,
                              'num_pages': num_pages,
                              'number': number,
                              'offset': offset,
                              'has_next': has_next,
                              'has_previous': has_previous,
                              'cba_trainer_labels': cba_trainer_labels,
                              'cba_trainer_values': cba_trainer_values,
                              'clinic_trainer_labels': clinic_trainer_labels,
                              'clinic_trainer_values': clinic_trainer_values,
                              'hub_trainer_labels': hub_trainer_labels,
                              'hub_trainer_values': hub_trainer_values,
                              'dho_trainer_labels': dho_trainer_labels,
                              'dho_trainer_values': dho_trainer_values,
                              'pho_trainer_labels': pho_trainer_labels,
                              'pho_trainer_values': pho_trainer_values,
                              'hub_total': hub_total,
                              'pho_total': pho_total,
                              'dho_total': dho_total,
                              'cba_total': cba_total,
                              'clinic_total': clinic_total,
                              'name_dir': name_dir,
                              'phone_dir': phone_dir,
                              'email_dir': email_dir,
                              'location_dir': location_dir,
                              'type_dir': type_dir,
                              'trained_by_dir': trained_by_dir,
                              'date_dir': date_dir,
                              'additional_text_dir': additional_text_dir,

                              }, context_instance=RequestContext(request)
                              )

