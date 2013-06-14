from django.conf.urls.defaults import patterns, url, include

import coachreports.api_urls

urlpatterns = patterns('coachreports.views',
    url(r'^$', 'coach_reports', {}, 'coach_reports'),
    url(r'^test/$', 'scatter', {}, 'scatter'),
#    url(r'(?P<subject_id>\w+)/(?P<topic_id>\w+)/mastery$',  'coach_reports', {}, 'coach_reports'),
#    url(r'(?P<student_id>\w+)/scatter$', 'scatter_data', {}, 'scatter_data'),
#    url(r'(?P<subject_id>\w+)/(?P<topic_id>\w+)/effort$',  'scatter_data', {}, 'scatter_effort'),
#    url(r'(?P<subject_id>\w+)/(?P<topic_id>\w+)/(?P<exercise_id>\w+)/scatter$', 'scatter_data', {}, 'scatter_data'),

    url(r'^api/', include(coachreports.api_urls)),
)

