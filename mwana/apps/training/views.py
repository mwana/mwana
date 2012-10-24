# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.training.models import Trained
from mwana.apps.training.forms import TrainedForm
from mwana.apps.issuetracking.issuehelper import IssueHelper
from datetime import datetime, date
from django.contrib.csrf.middleware import csrf_response_exempt, csrf_view_exempt

from django.template import RequestContext
from django.shortcuts import render_to_response
from mwana.apps.reports.webreports.models import ReportingGroup





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
        value = request.REQUEST[param].strip()
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

def get_admin_email_address():
    from djappsettings import settings
    try:
        return settings.ADMINS[0][1]
    except:
        return "Admin's email address"




@csrf_response_exempt
@csrf_view_exempt
def trained(request):
    order = read_request(request, "o")
    dir = read_request(request, "ot")
    navigation = read_request(request, "navigate")
    page = read_request(request, "page")
    sort = "location"
    direction = ""
    try:
        sort = {'1':'name', '2':'location', '3':'type', '4':'email', '5':'phone', '6':'date', '7':'trained_by', '8':'additional_text'}[order]
        direction = {'asc':'', 'desc':'-'}[dir]
    except:
        pass


    page = get_default_int(page)
    page = page + get_next_navigation(navigation)

    form =  TrainedForm() # An unbound form
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
            if not email:email=None


            model = Trained(name=name, phone=phone, email=email,
            trained_by=trained_by, type=type, date=date, location=location)


            model.save()


            form = TrainedForm() # An unbound form




    issueHelper = IssueHelper()

    (query_set, num_pages, number, has_next, has_previous) = issueHelper.get_trained_people("%s%s"% (direction, sort), page)


    return render_to_response('training/trained.html',
                              {
                              'form': form,
                              'model': 'Trained people',
                              'query_set': query_set,
                              'num_pages': num_pages,
                              'number': number,
                              'has_next': has_next,
                              'has_previous': has_previous,
                              }, context_instance=RequestContext(request)
                              )

