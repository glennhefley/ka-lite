import re, json, sys, logging
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from main.models import VideoLog, ExerciseLog, VideoFile
from securesync.models import Facility, FacilityUser,FacilityGroup, DeviceZone, Device
from utils.decorators import require_admin
from securesync.views import facility_required
from shared.views import group_report_context

from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.template.loader import render_to_string

from coachreports.forms import DataForm


#@require_admin
#@facility_required
@render_to("coachreports/scatter_view.html")
def scatter(request):
    # fake data
    form = DataForm(data={ 'facility_id': 1 })
    
    return {
        "form": form,
    }        
    

@require_admin
@facility_required
@render_to("coachreports/coach_reports.html")
def coach_reports(request, facility):


    return group_report_context(
        facility_id=facility.id, 
        group_id=request.REQUEST.get("group", ""), 
        topic_id=request.REQUEST.get("topic", ""), 
    )


@require_admin
@facility_required
@render_to("coachreports/scatter.html")
def scatter_data(request, facility, subject_id, topic_id=None, exercise_id=None, xaxis=None, yaxis=None):
    groups = FacilityGroup.objects.filter(facility=facility)
    selected_groups = [groups[0]]
    
    xaxis = xaxis or request.REQUEST.get("xaxis", "mastery")
    yaxis = xaxis or request.REQUEST.get("yaxis", "effort")
    
    users = dict()
    for user_obj in  FacilityUser.objects.filter(group in selected_groups).order_by("group.name", "last_name", "first_name"):
        users[user_obj.id] = {
            'first_name': user_obj.first_name,
            'last_name': user_obj.last_name,
            'group': user_obj.group.name,
            'xval': 0,
            'yval': 0,
        }

    return {
        "users": users,
        "groups": groups,
        "selected_groups": selected_groups,
        "xaxis": xaxis,
        "yaxis": yaxis,
    }


