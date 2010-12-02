# vim: ai ts=4 sts=4 et sw=4
from django.http import HttpResponse
from rapidsms.errors import NoRouterError
from . import utils
from rapidsms.contrib.ajax.exceptions import RouterNotResponding
from django.template import RequestContext
from django.shortcuts import render_to_response
from mwana.apps.echo.handlers import ping

def index(request):
    from rapidsms.router import router
    out = ''
    
    try:
        router_available = True
        statuses = utils.get_backend_status()

    except RouterNotResponding:
        router_available = False
        router_status = None
        
        
        
    if not router_available:
        out = 'Router: <b>DOWN</b> <br />'
        return HttpResponse(out)
    else:
        out = 'Router: UP <br />'
        
        
    inet_status = ping.ping_the_net()
    if inet_status:
        out += 'Internet: UP <br /><br />'
    else:
        out += 'Internet: DOWN <br /><br />'
#    statuses = statuses[1:-1]
#    statuses = statuses.split(',')
#    dd = {} #make a dict out of the statuses (there must be a better way?)
#    for kv in statuses:
#        v = kv.split(':')
#        v[0] = v[0].strip("'").strip()
#        v[1] = v[1].strip("'").strip()
#        dd[v[0]] = v[1]
    
    #TODO TURN ME INTO A DJANGO TEMPLATE USING VIEW!
    out += "<table border=1>"\
                "<tr>"\
                    "<td><b>Backend Statuses</b></td>"\
                "</tr>"
                
    
#    for i in dd:
    out += "<tr>"
#    out += '<td>'+str(i).strip("'")+'</td><td>'+str(dd[i]).strip("'")+"</td>"
    out += '<td>' + str(statuses) + '</td>' 
    out += "</tr>"
    
    return HttpResponse(out)
#    return render_to_response("echo/sometemplate.html",{'key':'value'},context_instance=RequestContext(request))

