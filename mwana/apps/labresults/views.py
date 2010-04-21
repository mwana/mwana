import json
import datetime

from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from mwana.apps.labresults import models as labresults
from mwana.decorators import has_perm_or_basicauth


@require_http_methods(['POST'])
@has_perm_or_basicauth('labresults.add_rawresult', 'Lab Results')
def accept_results(request):
    """
    Accepts incoming results from the lab via HTTP POST.  Example usage:
    
    import urllib
    import urllib2
    
    # set up authentication info
    authinfo = urllib2.HTTPBasicAuthHandler()
    authinfo.add_password(realm='Lab Results',
                          uri='http://localhost:8000/',
                          user='adh',
                          passwd='abc')
    
    opener = urllib2.build_opener(authinfo)
    urllib2.install_opener(opener)
    data = urllib.urlencode({'varname': 'value'})
    f = urllib2.urlopen('http://localhost:8000/labresults/incoming/', data)
    """
    labresults.RawResult.objects.create(date=datetime.datetime.now(),
                                        data=json.dumps(request.POST))
    return HttpResponse()
