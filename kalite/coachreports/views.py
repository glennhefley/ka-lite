import json
import requests
import datetime
from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from functools import partial

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
from utils.topic_tools import get_topic_exercises, get_topic_videos

def get_api_data(request, form=None, form_data=None):
    api_url = "http%s://%s%s" % ("s" if request.is_secure() else "", request.get_host(), reverse("coachreports.api_views.api_data"))

    if not form_data:
        if not form:
            form = get_data_form(request)
        form_data = form.data
    
    # Make the api request on the server-side,
    #   this is a good way to test the API while under development
    #   (rather than calling the function directly)
    response = requests.post(api_url, data=form_data)
    if response.status_code != 200:
        raise StatusException(message=response.text, status_code=response.status_code)

    data = json.loads(response.text)
    return data 


#@require_admin
@require_login
@facility_required
@render_to("coachreports/scatter_view.html")
def scatter_view(request, facility, xaxis="", yaxis=""):
    return scatter_view_context(request, facility=facility, xaxis=xaxis, yaxis=yaxis)

def get_accessible_objects_from_request(request, facility):

    # Options to select.  Note that this depends on the user.
    if request.user.is_superuser:
        groups = FacilityGroup.objects.filter(facility=facility)
        facilities = Facility.objects.all()
    elif "facility_user" in request.session:
        user = request.session["facility_user"]
        facilities = [user.facility]
        if user.group:
            groups = [request.session["facility_user"].group]
        else:
            groups = FacilityGroup.objects.filter(facility=facility)
    else:
        facilities = [facility]
        groups = FacilityGroup.objects.filter(facility=facility)

    return (groups, facilities)
            

def scatter_view_context(request, facility, topic_path="/topics/math/arithmetic/", *args, **kwargs):

    # Get the form, and retrieve the API data
    form = get_data_form(request, facility=facility, topic_path=topic_path, *args, **kwargs)

    (groups, facilities) = get_accessible_objects_from_request(request, facility)

    return {
        "form": form.data,
        "stats": stats_dict,
        "groups": groups,
        "facilities": facilities,
    }
    

@require_login
@facility_required
@render_to("coachreports/timeline_view.html")
def timeline_view(request, facility, xaxis="", yaxis=""):
    return scatter_view_context(request, facility=facility, xaxis=xaxis, yaxis=yaxis)

@require_login
@facility_required
@render_to("coachreports/student_view.html")
def student_view(request, facility, xaxis="pct_mastery", yaxis="ex:attempts"):
    user = request.session["facility_user"]
    
    topics = get_all_topics() # piss poor topics 
    topic_ids = [t['id'] for t in topics]
    topics = filter(partial(lambda n,ids: n['id'] in ids, ids=topic_ids), topicdata.NODE_CACHE['Topic'].values()) # real data, like paths
    
    exercise_logs = dict()
    video_logs = dict()
    exercise_sparklines = dict()
    stats = dict()
    for topic in topics:

        topic_exercises = get_topic_exercises(path=topic['path'])
        n_exercises = len(topic_exercises)
        exercise_logs[topic['id']] = ExerciseLog.objects.filter(user=user, exercise_id__in=[t['name'] for t in topic_exercises]).order_by("completion_timestamp")
        n_exercises_touched = len(exercise_logs[topic['id']])


        topic_videos = get_topic_videos(topic_id=topic['id'])
        n_videos = len(topic_videos)
        video_logs[topic['id']] = VideoLog.objects.filter(user=user, youtube_id__in=[tv['youtube_id'] for tv in topic_videos]).order_by("completion_timestamp")
        n_videos_touched = len(video_logs[topic['id']])
        
        exercise_sparklines[topic['id']] = [el.completion_timestamp for el in filter(lambda n: n.complete, exercise_logs[topic['id']])]
        
        stats[topic['id']] = {
            "pct_started":      0 if not n_exercises_touched else n_exercises_touched/float(n_exercises),
            "average_points":   0 if not n_exercises_touched else sum([el.points for el in exercise_logs[topic['id']]])/float(n_exercises_touched),
            "average_attempts": 0 if not n_exercises_touched else sum([el.attempts for el in exercise_logs[topic['id']]])/float(n_exercises_touched),
            "pct_mastery":      0 if not n_exercises_touched else sum([el.complete for el in exercise_logs[topic['id']]])/float(n_exercises_touched),
            "total_struggling": 0 if not n_exercises_touched else sum([el.struggling for el in exercise_logs[topic['id']]]),
            "last_completed":None if not n_exercises_touched else max([el.completion_timestamp or datetime.datetime(year=1900, month=1, day=1) for el in exercise_logs[topic['id']]]),
        }

    context = scatter_view_context(request, facility)
    return {
        "form": context["form"],
        "groups": context["groups"],
        "facilities": context["facilities"],
        "user": user,
        "topics": topics,
        "topic_ids": topic_ids,
        "exercise_logs": exercise_logs,
        "video_logs": video_logs,
        "exercise_sparklines": exercise_sparklines,
        "stats": stats,
        "stat_defs": [
            {"key": "pct_started",      "title": "% Started",        "type": "pct"},
            {"key": "average_points",   "title": "Average Points",   "type": "float"},
            {"key": "average_attempts", "title": "Average Attempts", "type": "float"},
            {"key": "pct_mastery",      "title": "% Mastery",        "type": "pct"},
            {"key": "total_struggling", "title": "Total Struggling", "type": "int"},
            {"key": "last_completed", "title": "Last Completed", "type": "date"},
        ]
    }

@require_login
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
    return scatter_view_context(request, facility=facility)


@render_to("coachreports/test.html")
def test(request):
    return {}

def get_all_topics():
    topics = topicdata.EXERCISE_TOPICS["topics"].values()
    topics = sorted(topics, key = lambda k: (k["y"], k["x"]))
    return topics

@facility_required
@render_to("coachreports/table_view.html")
def old_coach_report(request, facility, report_type="exercise"):
    import re, settings
    from utils.topic_tools import get_topic_videos, get_topic_exercises
    
    # Get a list of topics (sorted) and groups
    topics = get_all_topics()
    groups = FacilityGroup.objects.filter(facility=facility)
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
        
        # More code, but much faster
        exercise_names = [ex["name"] for ex in context["exercises"]]
        # Get students
        context["students"] = []
        for user in users:
            exlogs = ExerciseLog.objects.filter(user=user, exercise_id__in=exercise_names)
            log_ids = [log.exercise_id for log in exlogs]
            log_table = []
            for en in exercise_names:
                if en in log_ids:
                    log_table.append(exlogs[log_ids.index(en)])
                else:
                    log_table.append(None)
            
            context["students"].append({
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "exercise_logs": log_table,
            })

    elif report_type=="video":
        # Fill in videos
        context["videos"] = get_topic_videos(topic_id=topic_id)

        # More code, but much faster
        video_ids = [vid["youtube_id"] for vid in context["videos"]]
        # Get students
        context["students"] = []
        for user in users:
            vidlogs = VideoLog.objects.filter(user=user, youtube_id__in=video_ids)
            log_ids = [log.youtube_id for log in vidlogs]
            log_table = []
            for yid in video_ids:
                if yid in log_ids:
                    log_table.append(vidlogs[log_ids.index(yid)])
                else:
                    log_table.append(None)
            
            context["students"].append({
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "video_logs": log_table,
            })        
    else:
        return HttpResponseNotFound(render_to_string("404_distributed.html", {}, context_instance=RequestContext(request)))

    return context

