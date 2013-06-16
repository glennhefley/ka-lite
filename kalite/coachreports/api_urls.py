from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns('coachreports.api_views',
    url(r'data/$',      'api_data', {}, 'api_data'),
    url(r'^data/(?P<xaxis>\w+)/(?P<yaxis>\w+)/$', 'api_data', {}, 'api_data_2'),
#    url(r'friendly/$',  'api_friendly_names', {}, 'api_friendly_names'),
)

