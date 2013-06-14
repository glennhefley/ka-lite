import re, json, sys, logging
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from main.models import VideoLog, ExerciseLog, VideoFile
from securesync.models import Facility, FacilityUser,FacilityGroup, DeviceZone, Device
from utils.decorators import require_admin
from securesync.views import facility_required


@require_admin
@facility_required
@render_to("coachreports/coach_reports.html")
def coach_reports(request, facility):
    return group_report_context(
        facility_id=facility.id, 
        group_id=request.REQUEST.get("group", ""), 
        topic_id=request.REQUEST.get("topic", ""), 
    )
