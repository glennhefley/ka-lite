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
    data     = dict(zip([w.id for w in who], (dict(),)*len(who)))
    vid_logs = dict(zip([w.id for w in who], (None,)*len(who)))
    ex_logs  = dict(zip([w.id for w in who], (None,)*len(who)))

    # Set up queries (but don't run them), so we have really easy aliases.
    #   Only do them if they haven't been done yet (tell this by passing in a value to the lambda function)      
    # Topics: topics.
    # Exercises: names (ids for ExerciseLog objects)
    # Videos: youtube_id (ids for VideoLog objects)
    search_fun      = partial(lambda t,p: t["path"].startswith(p), p=where)
    query_topics    = partial(lambda t,sf: t if t is not None else [t           for t   in filter(sf, topicdata.NODE_CACHE['Topic'].values())],sf=search_fun)
    query_exercises = partial(lambda e,sf: e if e is not None else [ex["name"]  for ex  in filter(sf, topicdata.NODE_CACHE['Exercise'].values())],sf=search_fun)
    query_videos    = partial(lambda v,sf: v if v is not None else [vid["youtube_id"] for vid in filter(sf, topicdata.NODE_CACHE['Video'].values())],sf=search_fun)

    # Exercise log and video log dictionary (key: user)
    query_exlogs    = lambda u,ex,el: el if el is not None else ExerciseLog.objects.filter(user=u, exercise_id__in=ex)
    query_vidlogs   = lambda u,vid,vl: vl if vl is not None else VideoLog.objects.filter(user=u, youtube_id__in=vid)
    
    # No users, don't bother.
    if len(who)>0:
        for type in (types if not hasattr(types,"lower") else [types]): # convert list from string, if necessary
            if type in data[data.keys()[0]]:
                continue
            
            if type == "pct_mastery":
                exercises = query_exercises(exercises)
            
                # Efficient query out, spread out to dict
                # ExerciseLog.filter(user__in=who, exercise_id__in=exercises).order_by("user.id")
                for user in data.keys():
                    ex_logs[user] = query_exlogs(user, exercises, ex_logs[user])
                    data[user][type] = sum([el.complete for el in ex_logs[user]])/ex_logs[user].count()

            elif type == "effort":
                if "ex.attempts" in data[data.keys()[0]] and "vid.total_seconds_watched" in data[data.keys()[0]]:
                    for user in data.keys():
                        total_attempts = sum(data[user]["ex.attempts"].values())
                        total_seconds_watched = sum(data[user]["vid.total_seconds_watched"].values())
                        data[user][type] = total_attempts/10 + total_seconds_watched/750
                else:
                    types += ["ex.attempts", "vid.total_seconds_watched", "effort"]
            

            # Just querying out data directly: Exercise
            elif type.startswith("vid.") and type[4:] in [f.name for f in VideoLog._meta.fields]:
                videos = query_videos(videos)
                for user in data.keys():
                    vid_logs[user] = query_vidlogs(user, videos, vid_logs[user])
                    data[user][type] = dict(zip(videos, [getattr(v, type[4:]) for v in vid_logs[user]]))
        
            # Just querying out data directly: Exercise
            elif type.startswith("ex.") and type[3:] in [f.name for f in ExerciseLog._meta.fields]:
                exercises = query_exercises(exercises)
                for user in data.keys():
                    ex_logs[user] = query_exlogs(user, exercises, ex_logs[user])
                    data[user][type] = dict(zip(exercises, [getattr(e,type[3:]) for e in ex_logs[user]]))
        
            else:
                raise Exception("Unknown type: %s" % type)

    return {
        "data": data,
        "topics": topics,
        "exercises": exercises,
        "videos": videos,
    }



@csrf_exempt
@render_to("test.html")
def api_data(request):
#    if request.method != "POST":
#        return HttpResponseForbidden("%s request not allowed." % request.method)
    
    # Get the request form
    form = DataForm(data=request.REQUEST)

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
        groups = FacilityGroup.objects.filter(facility__in=form.data.get("facility_id"))
        users = FacilityUser.objects.filter(group__in=groups)
    else:
        return HttpResponseNotFound("Did not specify facility, group, nor user.", status_code=404)

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
        "groups": [g.name for g in groups],
    }
    
    # Now we have data, stream it back
    return HttpResponse(content=json.dumps(json_data), content_type="application/json")
    
    
    
    
    