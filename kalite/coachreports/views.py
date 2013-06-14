import json
import requests
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.template.loader import render_to_string

from main.models import VideoLog, ExerciseLog, VideoFile
from securesync.models import Facility, FacilityUser,FacilityGroup, DeviceZone, Device
from utils.decorators import require_admin
from securesync.views import facility_required
from shared.views import group_report_context
from coachreports.forms import DataForm


#@require_admin
@render_to("coachreports/scatter_view.html")
def scatter(request):

    # fake data
    form = DataForm(data = { # the following defaults are for debug purposes only
        'facility_id': request.REQUEST.get('facility_id', Facility.objects.filter(name__contains="Wilson Elementary")[0].id),
        'group_id':    request.REQUEST.get('group_id',    FacilityGroup.objects.all()[0].id),
        'user':        request.REQUEST.get('user_id',     ""),
        'topic_path':  request.REQUEST.get('topic_path',  "/topics/math/arithmetic/multiplication-division/"),
        'xaxis':       request.REQUEST.get('xaxis',       "pct_mastery"),
        'yaxis':       request.REQUEST.get('yaxis',       "effort"  ),
    })

    api_url = "http%s://%s%s" % ("s" if request.is_secure() else "", request.get_host(), reverse("coachreports.api_views.api_data"))

    # Make the api request on the server-side
    response = requests.post(api_url, data=form.data)

    if response.status_code == 404:
        return HttpResponseNotFound(response.text)
    elif response.status_code != 200:
        return HttpResponseServerError(response.text)

    data = json.loads(response.text)
    
    return {
        "form": form.data,
        "data": data,
    }        
    

@require_admin
@render_to("coachreports/landing_page.html")
def landing_page(request):

    return {
    }


