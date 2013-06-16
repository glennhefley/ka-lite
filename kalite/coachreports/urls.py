from django.conf.urls.defaults import patterns, url, include

import coachreports.api_urls

urlpatterns = patterns('coachreports.views',
    url(r'^$', 'landing_page', {}, 'coach_reports'),
    url(r'^scatter/$', 'scatter_view', {}, 'scatter_view'),
    url(r'^scatter/(?P<xaxis>\w+)/(?P<yaxis>\w+)/$', 'scatter_view', {}, 'scatter_view'),
    url(r'^table/$',   'table_view', {}, 'table_view'),
#    url(r'^student/$', 'student_view', {}, 'student_view'),

    url(r'^old/$', 'old_coach_report', {}, 'old_coach_report'),
    url(r'^old/(?P<report_type>\w+)/$', 'old_coach_report', {}, 'old_coach_report'),

#    url(r'(?P<subject_id>\w+)/(?P<topic_id>\w+)/mastery$',  'coach_reports', {}, 'coach_reports'),
#    url(r'(?P<student_id>\w+)/scatter$', 'scatter_data', {}, 'scatter_data'),
#    url(r'(?P<subject_id>\w+)/(?P<topic_id>\w+)/effort$',  'scatter_data', {}, 'scatter_effort'),
#    url(r'(?P<subject_id>\w+)/(?P<topic_id>\w+)/(?P<exercise_id>\w+)/scatter$', 'scatter_data', {}, 'scatter_data'),

    url(r'^api/', include(coachreports.api_urls)),
)

