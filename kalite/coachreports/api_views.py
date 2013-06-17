import re, json, sys, logging
from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from functools import partial

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt, csrf_protect


from main.models import VideoLog, ExerciseLog, VideoFile
from securesync.models import Facility, FacilityUser,FacilityGroup, DeviceZone, Device
from utils.decorators import require_admin
from securesync.views import facility_required
#from shared.views import group_report_context
from coachreports.forms import DataForm
from main import topicdata
from config.models import Settings


class StatusException(Exception):
    def __init__(self, message, status_code):
        super(StatusException, self).__init__(message)
        self.args = (status_code,)
        self.status_code = status_code

def get_data_form(request, *args, **kwargs):
    """Request objects get priority over keyword args"""
    assert not args, "all non-request args should be keyword args"
    
    # Pull the form parameters out of the request or 
    data = dict()
    for field in ["facility_id", "group_id", "user_id", "xaxis", "yaxis"]:
        # Default to empty string, as it makes template handling cleaner later.
        data[field] = request.REQUEST.get(field, kwargs.get(field, ""))
    data["topic_path"] = request.REQUEST.getlist("topic_path")
    form = DataForm(data = data)
    
    # get the selected facility from the arg passed by @facility_required, if needed
    if not form.data["facility_id"]:
        form.data["facility_id"] = getattr(kwargs["facility"], "id", "")
                
    if "facility_user" in request.session:
        user = request.session["facility_user"]
        group = None if not user else user.group
        facility = None if not user else user.facility
        
        # Fill in default query data
        if not (form.data["facility_id"] or form.data["group_id"] or form.data["user_id"]):
        
            # Defaults:
            #   Students: only themselves
            #   Teachers: if nothing is specified, then show their group
        
            if request.is_admin:
                if group:
                    form.data["group_id"] = group.id
                elif facility:
                    form.data["facility_id"] = facility.id
                else: # not a meaningful default, but responds efficiently (no data)
                    form.data["user_id"] = user.id
            else:
                form.data["user_id"] = user.id    
        
        # Authenticate
        if group and form.data["group_id"] and group.id != form.data["group_id"]: # can't go outside group
            # We could also redirect
            HttpResponseForbidden("You cannot choose a group outside of your group.")
        elif facility and form.data["facility_id"] and facility.id != form.data["facility_id"]:
            # We could also redirect
            HttpResponseForbidden("You cannot choose a facility outside of your own facility.")
        elif not request.is_admin:
            if not form.data["user_id"]:
                # We could also redirect
                HttpResponseForbidden("You cannot choose facility/group-wide data.")
            elif user and form.data["user_id"] and user.id != form.data["user_id"]:
                # We could also redirect
                HttpResponseForbidden("You cannot choose a user outside of yourself.")
    
    return form    

def compute_data(types, who, where):
    """
    Compute the data in "types" for each user in "who", for the topics selected by "where"
    
    who: list of users
    where: topic_path
    types can include:
        pct_mastery
        effort
        attempts
    """
    
    # None indicates that the data hasn't been queried yet.
    #   We'll query it on demand, for efficiency
    topics = None
    exercises = None
    videos = None

    # Initialize an empty dictionary of data, video logs, exercise logs, for each user
    data     = dict(zip([w.id for w in who], [dict() for i in range(len(who))]))
    vid_logs = dict(zip([w.id for w in who], [None   for i in range(len(who))]))
    ex_logs  = dict(zip([w.id for w in who], [None   for i in range(len(who))]))

    # Set up queries (but don't run them), so we have really easy aliases.
    #   Only do them if they haven't been done yet (tell this by passing in a value to the lambda function)      
    # Topics: topics.
    # Exercises: names (ids for ExerciseLog objects)
    # Videos: youtube_id (ids for VideoLog objects)
    search_fun      = partial(lambda t,p: t["path"].startswith(p), p=tuple(where))
    query_topics    = partial(lambda t,sf: t if t is not None else [t           for t   in filter(sf, topicdata.NODE_CACHE['Topic'].values())],sf=search_fun)
    query_exercises = partial(lambda e,sf: e if e is not None else [ex["name"]  for ex  in filter(sf, topicdata.NODE_CACHE['Exercise'].values())],sf=search_fun)
    query_videos    = partial(lambda v,sf: v if v is not None else [vid["youtube_id"] for vid in filter(sf, topicdata.NODE_CACHE['Video'].values())],sf=search_fun)

    # Exercise log and video log dictionary (key: user)
    query_exlogs    = lambda u,ex,el:  el if el is not None else ExerciseLog.objects.filter(user=u, exercise_id__in=ex)
    query_vidlogs   = lambda u,vid,vl: vl if vl is not None else VideoLog.objects.filter(user=u, youtube_id__in=vid)
    
    # No users, don't bother.
    if len(who)>0:
        for type in (types if not hasattr(types,"lower") else [types]): # convert list from string, if necessary
            if type in data[data.keys()[0]]: # if the first user has it, then all do; no need to calc again.
                continue
            
            if type == "pct_mastery":
                exercises = query_exercises(exercises)
            
                # Efficient query out, spread out to dict
                # ExerciseLog.filter(user__in=who, exercise_id__in=exercises).order_by("user.id")
                for user in data.keys():
                    ex_logs[user] = query_exlogs(user, exercises, ex_logs[user]) 
                    data[user][type] = 0 if not ex_logs[user] else 100.*sum([el.complete for el in ex_logs[user]])/float(len(exercises))
                    
            elif type == "effort":
                if "ex:attempts" in data[data.keys()[0]] and "vid:total_seconds_watched" in data[data.keys()[0]]:
                    for user in data.keys():
                        avg_attempts = sum(data[user]["ex:attempts"].values())/float(len(exercises))
                        avg_seconds_watched = sum(data[user]["vid:total_seconds_watched"].values())/float(len(videos))
                        data[user][type] = avg_attempts/10. + avg_seconds_watched/750.
                else:
                    types += ["ex:attempts", "vid:total_seconds_watched", "effort"]
            

            # Just querying out data directly: Video
            elif type.startswith("vid:") and type[4:] in [f.name for f in VideoLog._meta.fields]:
                videos = query_videos(videos)
                for user in data.keys():
                    vid_logs[user] = query_vidlogs(user, videos, vid_logs[user])
                    data[user][type] = dict([(v.youtube_id, getattr(v, type[4:])) for v in vid_logs[user]])
        
            # Just querying out data directly: Exercise
            elif type.startswith("ex:") and type[3:] in [f.name for f in ExerciseLog._meta.fields]:
                exercises = query_exercises(exercises)
                for user in data.keys():
                    ex_logs[user] = query_exlogs(user, exercises, ex_logs[user])
                    data[user][type] = dict([(el.exercise_id, getattr(el,type[3:])) for el in ex_logs[user]])
            
            # Unknown requested quantity     
            else:
                raise Exception("Unknown type: %s not in %s" % (type, str([f.name for f in ExerciseLog._meta.fields])))

    return {
        "data": data,
        "topics": topics,
        "exercises": exercises,
        "videos": videos,
    }


"""
def get_data_form(request):
    # fake data
    form = DataForm(data = { # the following defaults are for debug purposes only
        'facility_id': request.REQUEST.get('facility_id'), #Facility.objects.filter(name__contains="Wilson Elementary")[0].id),
        'group_id':    request.REQUEST.get('group_id'),#FacilityGroup.objects.all()[0].id),
        'user_id':     request.REQUEST.get('user_id'),
        'topic_path':  request.REQUEST.get('topic_path'),#,  "/topics/math/arithmetic/multiplication-division/"),
        'xaxis':       request.REQUEST.get('xaxis'),#,       "pct_mastery"),
        'yaxis':       request.REQUEST.get('yaxis'),#,       "effort"  ),
    })

    return form
"""    
    
@csrf_exempt
def api_data(request, xaxis="", yaxis=""):
#    if request.method != "POST":
#        return HttpResponseForbidden("%s request not allowed." % request.method)
    
    # Get the request form
    form = get_data_form(request, xaxis=xaxis, yaxis=yaxis)#(data=request.REQUEST)

    # Query out the data: who?
    if form.data.get("user_id"):
        facility = []
        groups = []
        users = [get_object_or_404(FacilityUser, id=form.data.get("user_id"))]
    elif form.data.get("group_id"):
        facility = []
        groups = [get_object_or_404(FacilityGroup, id=form.data.get("group_id"))]
        users = FacilityUser.objects.filter(group=form.data.get("group_id"))
    elif form.data.get("facility_id"):
        facility = get_object_or_404(Facility, id=form.data.get("facility_id"))
        groups = FacilityGroup.objects.filter(facility__in=[form.data.get("facility_id")])
        users = FacilityUser.objects.filter(group__in=groups)
    else:
        return HttpResponseNotFound("Did not specify facility, group, nor user.")

    # Query out the data: where?
    if not form.data.get("topic_path"):
        return HttpResponseServerError("Must specify a topic path")

    # Query out the data: what?
    computed_data = compute_data(types=[form.data.get("xaxis"), form.data.get("yaxis")], who=users, where=form.data.get("topic_path"))
    json_data = {
        "data": computed_data["data"],
        "exercises": computed_data["exercises"],
        "videos": computed_data["videos"],
        "users": dict( zip( [u.id for u in users],
                            ["%s, %s" % (u.first_name, u.last_name) for u in users]
                     )),
        "groups":  dict( zip( [g.id for g in groups],
                             dict(zip(["id", "name"], [(g.id, g.name) for g in groups])),
                      )),
        "facility": None if not facility else {
            "name": facility.name,
            "id": facility.id,
        }
    }
    
    # Now we have data, stream it back
    return HttpResponse(content=json.dumps(json_data), content_type="application/json")
    
    
    
@csrf_exempt
def api_friendly_names(request):
    """api_data returns raw data with identifiers.  This endpoint is a generic endpoint
    for mapping IDs to friendly names."""
    
    
    return None