from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('coachreports.views',
    url(r'^$', 'coach_reports', {}, 'coach_reports'),
)

