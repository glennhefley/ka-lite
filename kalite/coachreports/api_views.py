import re, json, sys, logging
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.template.loader import render_to_string


from main.models import VideoLog, ExerciseLog, VideoFile
from securesync.models import Facility, FacilityUser,FacilityGroup, DeviceZone, Device
from utils.decorators import require_admin
from securesync.views import facility_required
#from shared.views import group_report_context
from coachreports.forms import DataForm

@render_to("test.html")
def api_data(request):
    if request.method != "POST":
        return HttpResponseForbidden("%s request not allowed." % request.method)
    
    form = DataForm(data=request.POST)
