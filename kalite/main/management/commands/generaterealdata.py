"""
# Data design:
#
# We want:
#   * more data (over a larger set of topics, showing progression/mastery?)
#   * user data generated from underlying variables:
#     - speed_of_learning (0 to 1, mean 0.5)
#     - effort_level (0 to 1, mean 0.5)
#     - time_in_program (determines # of samples)
#   * three types of users:
#     - normal (60%)
#     - unchallenged (20%): high speed_of_learning, low effort_level
#     - struggling   (20%): low speed_of_learning, high effort_level
"""

from django.core.management.base import BaseCommand, CommandError
from securesync.models import Facility, FacilityUser, FacilityGroup, Device, DeviceMetadata
import securesync
from main.models import ExerciseLog, VideoLog
import random
import json
from math import exp, sqrt, ceil
from main import topicdata
import logging

import settings
from utils.topic_tools import get_topic_videos

firstnames = ["Richard","Kwame","Jamie","Alison","Nadia","Zenab","Guan","Dylan","Vicky","Melanie","Michelle","Yamira","Elena","Thomas","Jorge","Lucille","Arnold","Rachel","Daphne","Sofia"]

lastnames = ["Awolowo","Clement","Smith","Ramirez","Hussein","Wong","Franklin","Lopez","Brown","Paterson","De Soto","Khan","Mench","Merkel","Roschenko","Picard","Jones","French","Karnowski","Boyle"]

# We want to show some users that have a correlation between effort and mastery, some that show mastery without too much effort (unchallenged), and some that show little mastery with a lot of effort
user_types = [ { "name": "common",       "speed_of_learning": (0.5,1),     "effort_level": (0.5,1),     "time_in_program": (0.5, 1)},
               { "name": "unchallenged", "speed_of_learning": (0.75, 0.5), "effort_level": (0.25, 0.5), "time_in_program": (0.5, 1) },
               { "name": "struggling",   "speed_of_learning": (0.25, 0.5), "effort_level": (0.75, 0.5), "time_in_program": (0.5, 1) },
              ]

def select_all_exercises(topic_name):
    # This function needs to traverse all children (recursively?) to select out all exercises.
    # Note: this function may exist
    pass
    
topics = ["multiplication-division"]

def generate_user_type(n=1):
    # 0: 60%=common, 1: 20%=unchallenged; 2: 20%=struggling
    return [int(max(0, ceil(random.random()/0.2)-3)) for ni in range(n)]

def sample_user_settings():
    user_type = user_types[generate_user_type()[0]]
    return {
        "name": user_type["name"],
        "speed_of_learning": random.gauss(user_type["speed_of_learning"][0], user_type["speed_of_learning"][1]),
        "effort_level":      random.gauss(user_type["effort_level"][0],      user_type["effort_level"][1]),
        "time_in_program":   random.random()#(user_type["time_in_program"][0],   user_type["time_in_program"][1]),
    }
    
def username_from_name(first_name, last_name):
    return (first_name[0] + last_name).lower()
    
def sigmoid(theta, a, b):
    return 1.0 / (1.0 + exp(b - a * theta))


def generate_fake_facilities(names=("Wilson Elementary",)):
    """Add the given fake facilities"""
    facilities = [];
    
    for name in names:
        try:
            facility = Facility.objects.get(name=name)
            logging.info("Retrieved facility '%s'" % name)
        except Facility.DoesNotExist as e:
            facility = Facility(name=name)
            facility.save()
            logging.info("Created facility '%s'" % name)
        
        facilities.append(facility)
        
    return facilities


def generate_fake_facility_groups(names=("Class 4E", "Class 5B"), facilities=None):
    """Add the given fake facility groups to the given fake facilities"""
    
    if not facilities:
        facilities = generate_fake_facilities()
        
    facility_groups = [];
    for facility in facilities:
        for name in names:
            try:
                facility_group = FacilityGroup.objects.get(facility=facility, name=name)
                logging.info("Retrieved facility group '%s'" % name)
            except FacilityGroup.DoesNotExist as e:
                facility_group = FacilityGroup(facility=facility, name=name)
                facility_group.full_clean()
                facility_group.save()
                logging.info("Created facility group '%s'" % name)
            
            facility_groups.append(facility_group)
        
    return (facility_groups,facilities)
        
        
def generate_fake_facility_users(nusers=20, facilities=None, facility_groups=None, password="blah"):
    """Add the given fake facility users to each of the given fake facilities.
    If no facilities are given, they are created."""

    if not facility_groups:
        (facility_groups,facilities) = generate_fake_facility_groups(facilities=facilities)
               
    facility_users = []
    
    cur_usernum = 0
    users_per_group = nusers/len(facility_groups)
    
    for facility in facilities:
        for facility_group in facility_groups:
            for i in range(0,users_per_group):
                user_data = {
                    "first_name": random.choice(firstnames),
                    "last_name":  random.choice(lastnames),
                }
                user_data["username"] = username_from_name(user_data["first_name"], user_data["last_name"])
                   
                try:
                    facility_user = FacilityUser.objects.get(facility=facility, username=user_data["username"])
                    facility_user.group = facility_group
                    facility_user.save()
                    logging.info("Retrieved facility user '%s/%s'" % (facility.name,user_data["username"]))
                except FacilityUser.DoesNotExist as e:
                    notes = json.dumps(sample_user_settings())
                    
                    facility_user = FacilityUser(facility=facility, username=user_data["username"], first_name=user_data["first_name"], last_name=user_data["last_name"], notes=notes, group=facility_group)
                    facility_user.set_password(password) # set same password for every user
                    facility_user.full_clean()
                    facility_user.save()
                    logging.info("Created facility user '%s/%s'" % (facility.name,user_data["username"] ))
                
                facility_users.append(facility_user)
                
                cur_usernum += 1 # this is messy and could be done more intelligently; 
                                 # could also randomize to add more users, as this function
                                 # seems to be generic, but really is not.

    return (facility_users,facility_groups,facilities)
    

def generate_fake_exercise_logs(topics=topics,facility_users=None):
    """Add exercise logs for the given topics, for each of the given users.
    If no users are given, they are created.
    If no topics exist, they are taken from the list at the top of this file."""
    
    if not facility_users:
        (facility_users,_,_) = generate_fake_facility_users()
        
    exercise_logs = []
    
    for topic in topics:
        exercises = json.load(open("./static/data/topicdata/" + topic + ".json","r"))
        exercises = sorted(exercises, key = lambda k: (k["h_position"], k["v_position"]))
        
        for i, user in enumerate(facility_users):
            # Get (or create) user type
            try:
                user_settings = json.loads(user.notes)
            except:
                user_settings = sample_user_settings()
                user.notes = json.dumps(user_settings)
                user.save()
            
            #speed_of_learning, effort_level, time_in_program
            # Probability of doing any particular exercise
            p_exercise = 0.5*user_settings["effort_level"] + 0.5*user_settings["time_in_program"]
            
            # # of exercises is related to 
            for j, exercise in enumerate(exercises):
                if random.random() > p_exercise:
                    continue
                
                # 
                p_completed = 0.33*user_settings["effort_level"] + 0.66*user_settings["speed_of_learning"]
                p_attempts = 0.33*user_settings["effort_level"] + 0.55*user_settings["time_in_program"]
                
                attempts = random.random() * p_attempts * 30 + 10
                progress_sample = (p_completed - random.random())
                completed = (progress_sample > 0)
                streak_progress = 100 if completed else 100*progress_sample/(p_completed-1.0)
                points   = attempts * 10 * min(1, user_settings["speed_of_learning"]*1.5)
                
                # Always create new
                logging.info("Creating exercise log: %-12s: %-25s (%d points, %d attempts, %d%% streak)" % (user.first_name, exercise["name"],  int(points), int(attempts), int(streak_progress)))
                log = ExerciseLog(user=user, exercise_id=exercise["name"], attempts=int(attempts), streak_progress=int(streak_progress), points=int(points))
                log.full_clean()
                log.save()
                
                exercise_logs.append(log)

        return exercise_logs
        
        
def generate_fake_video_logs(topics=topics,facility_users=None):
    """Add video logs for the given topics, for each of the given users.
    If no users are given, they are created.
    If no topics exist, they are taken from the list at the top of this file."""
    
    if not facility_users:
        (facility_users,_,_) = generate_fake_facility_users()
        
    video_logs = []
    
    for topic in topics:
        videos = get_videos_for_topic(topic_id=topic)
        
        # Determine proficiency
        videos_a = [random.random() for i in range(len(videos))]
        videos_b = [float(i) / len(videos) for i in range(len(videos))]

        for i, user in enumerate(facility_users):
            for j, video in enumerate(videos):
                sig = sigmoid(proficiency[i], videos_a[j], videos_b[j])
                if random.random() > sig:
                    continue
                
                p_complete = sqrt(sqrt(sig))
                total_seconds_watched = video["duration"] if p_complete>=random.random() else video["duration"]*sqrt(random.random()*sig)
                points   = total_seconds_watched/10*10

                logging.info("Creating video log: %-12s: %-45s (%4.1f%% watched, %d points)%s" % (user.first_name, video["title"],  100*total_seconds_watched/video["duration"], int(points)," COMPLETE!" if int(total_seconds_watched)==video["duration"] else ""))
                log = VideoLog(user=user, youtube_id=video["youtube_id"], total_seconds_watched=int(total_seconds_watched), points=int(points))
                log.full_clean()
                log.save()
        
                video_logs.append(log)

        return video_logs
        
        
class Command(BaseCommand):
    args = "<data_type=[facility,facility_users,facility_groups,default=exercises,videos]>"

    help = "Generate fake user data.  Can be re-run to generate extra exercise and video data."

    def handle(self, *args, **options):
        logging.getLogger().setLevel(logging.INFO)
        
        # First arg is the type of data to generate
        generate_type = "exercises" if len(args)<=0 else args[0].lower()
                
        if "facility" == generate_type or "facilities" == generate_type: 
            generate_fake_facilities()
    
        elif "facility_groups" == generate_type: 
            generate_fake_facility_groups()
    
        elif "facility_users" == generate_type:
            generate_fake_facility_users() # default password
        
        elif "exercises" == generate_type:
            (facility_users,_,_) = generate_fake_facility_users() # default password
            generate_fake_exercise_logs(facility_users=facility_users)
            
        elif "videos" == generate_type:
            (facility_users,_,_) = generate_fake_facility_users() # default password
            generate_fake_video_logs(facility_users=facility_users)
            
        else:
            raise Exception("Unknown data type to generate: %s" % generate_type)

                