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
from utils.decorators import require_login
from securesync.views import facility_required
from shared.views import group_report_context
from coachreports.forms import DataForm
from main import topicdata
from coachreports.api_views import StatusException, get_data_form, stats_dict


"""
def get_api_data(request, form):
    api_url = "http%s://%s%s" % ("s" if request.is_secure() else "", request.get_host(), reverse("coachreports.api_views.api_data"))

    form = get_data_form(request)
    
    # Make the api request on the server-side,
    #   this is a good way to test the API while under development
    #   (rather than calling the function directly)
    response = requests.post(api_url, data=form.data)
    if response.status_code != 200:
        raise StatusException(message=response.text, status_code=response.status_code)

    data = json.loads(response.text)
    return data 
"""

#@require_admin
@facility_required
@render_to("coachreports/scatter_view.html")
def scatter_view(request, facility, xaxis="", yaxis=""):
    return scatter_view_context(request, facility=facility, xaxis=xaxis, yaxis=yaxis)


def scatter_view_context(request, facility, topic_path="/topics/math/arithmetic/", *args, **kwargs):

    # Get the form, and retrieve the API data
    form = get_data_form(request, facility=facility, topic_path=topic_path, *args, **kwargs)
        
    data = []
    try:
        pass#data = get_api_data(request, form)
    except StatusException as se:
        if se.status_code == 404:
            return HttpResponseNotFound(se.message)
        else:
            return HttpResponseServerError(se.message)
    
    groups = FacilityGroup.objects.filter(facility=facility)
    # The API tries to be lean and mean with it's response objects and text,
    #   and so mostly sends unique identifiers of objects, rather than
    #   full data / names.
    #
    # Let's expose an end-point for retrieving user-friendly names
    
    return {
        "form": form.data,
        "data": data,
        "stats": stats_dict,
        "groups": groups,
        "facility": facility,
    }
    

@facility_required
@render_to("coachreports/timeline_view.html")
def timeline_view(request, facility, xaxis="", yaxis=""):
    return scatter_view_context(request, facility=facility, xaxis=xaxis, yaxis=yaxis)

@facility_required
@render_to("coachreports/student_view.html")
def student_view(request, facility, xaxis="pct_mastery", yaxis="ex:attempts"):
    context = scatter_view_context(request, facility=facility, xaxis=xaxis, yaxis=yaxis)
    return context

#@require_admin
@facility_required
@render_to("coachreports/table_view.html")
def table_view(request, facility):

    form = get_data_form(request, facility=facility)
    try:
        data = get_api_data(request, form)
    except StatusException as se:
        if se.status_code == 404:
            return HttpResponseNotFound(se.message)
        else:
            return HttpResponseServerError(se.message)
    
    return {
        "form": form.data,
        "data": data,
    }        


@require_login
@facility_required
@render_to("coachreports/landing_page.html")
def landing_page(request, facility):

    form = get_data_form(request, facility=facility)
    if not form.data.get("topic_path"):
        form.data["topic_path"] = "/topics/math/arithmetic/"
        form.data["facility_id"] = facility.id
        
    return {
        "form": form.data
    }



@facility_required
@render_to("coachreports/old2.html")
def old_coach_report(request, facility, report_type="exercise"):
    import re, settings
    from utils.topic_tools import get_topic_videos, get_topic_exercises
    
    # Get a list of topics (sorted) and groups
    topics = topicdata.EXERCISE_TOPICS["topics"].values()
    topics = sorted(topics, key = lambda k: (k["y"], k["x"]))
    groups = FacilityGroup.objects.filter(facility=facility)
    paths = dict((key, val["path"]) for key, val in topicdata.NODE_CACHE["Exercise"].items())
    context = {
        "report_types": ("exercise","video"),
        "request_report_type": report_type,
        "facility": facility,
        "groups": groups,
        "topics": topics,
    }
    
    # get querystring info
    topic_id = request.GET.get("topic", "")
    group_id = request.GET.get("group", "")
    
    # No valid data; just show generic
    if not group_id or not topic_id or not re.match("^[\w\-]+$", topic_id):
        return context
 
    users = get_object_or_404(FacilityGroup, pk=group_id).facilityuser_set.order_by("last_name", "first_name")

    # We have enough data to render over a group of students
    # Get type-specific information
    if report_type=="exercise":
        # Fill in exercises
        exercises = get_topic_exercises(topic_id)
        context["exercises"] = exercises
        
        # Get students
        context["students"] = [{
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "exercise_logs": [get_object_or_None(ExerciseLog, user=user, exercise_id=ex["name"]) for ex in exercises],
        } for user in users]
    
    elif report_type=="video":
        # Fill in videos
        context["videos"] = get_topic_videos(topic_id)

        context["students"] = [{
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "video_logs": [get_object_or_None(VideoLog, user=user, youtube_id=v["youtube_id"]) for v in context["videos"]],
        } for user in users]
        
    else:
        return HttpResponseNotFound(render_to_string("404_distributed.html", {}, context_instance=RequestContext(request)))

    return context

