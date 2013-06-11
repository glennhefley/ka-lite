from django.http import HttpResponseRedirect
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

import securesync.urls
<<<<<<< HEAD
import shared.urls
=======
>>>>>>> origin/separate_server_code
from kalite import settings


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^images/(.+)$', lambda request, path: HttpResponseRedirect('/static/images/' + path)),
    url(r'^securesync/', include(securesync.urls)),
)

urlpatterns += patterns('',
<<<<<<< HEAD
    url(r'^' + settings.CONTENT_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.CONTENT_ROOT,
    }),
    url(r'^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_URL,
    }),
    url(r'^' + settings.STATIC_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {
=======
    url(r'^%s(?P<path>.*)$' % settings.CONTENT_URL[1:], 'django.views.static.serve', {
        'document_root': settings.CONTENT_ROOT,
    }),
    url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT,
    }),
    url(r'^%s(?P<path>.*)$' % settings.STATIC_URL[1:], 'django.views.static.serve', {
>>>>>>> origin/separate_server_code
        'document_root': settings.STATIC_ROOT,
    }),
)

# Javascript translations
urlpatterns += patterns('',
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('ka-lite.locale')}, 'i18n_javascript_catalog'),
)

urlpatterns += patterns('main.views',
    url(r'^exercisedashboard/$', 'exercise_dashboard', {}, 'exercise_dashboard'),
    url(r'^coachreports/$', 'coach_reports', {}, 'coach_reports'),
<<<<<<< HEAD
    url(r'^easyadmin/$', 'easy_admin', {}, 'easy_admin'),
    url(r'^stats/$', 'summary_stats', {}, 'summary_stats'),
    url(r'^$', 'homepage', {}, 'homepage'),
    url(r'^update/$', 'update', {}, 'update'),
    url(r'^userlist/$', 'user_list', {}, 'user_list'),

    # Zone, facility, device
    url(r'^zone/$', 'zone_discovery', {}, 'zone_discovery'), # only one zone, so make an easy way to access it
    url(r'^device/$', 'device_discovery', {}, 'device_discovery'), # only one device, so make an easy way to access it
    url(r'^(?P<org_id>\s{0})', include(shared.urls)), # no org_id, but parameter needed for reverse url look-up

    url(r'^api/', include('main.api_urls')),
)

if settings.AUTO_LOAD_TEST:
=======
    url(r'^$', 'homepage', {}, 'homepage'),
    url(r'^update/$', 'update', {}, 'update'),
    url(r'^userlist/$', 'user_list', {}, 'user_list'),
    url(r'^api/', include('main.api_urls')),
)

if getattr(settings, "AUTO_LOAD_TEST", None):
>>>>>>> origin/separate_server_code
    urlpatterns += patterns('main.views',
        url(r'^loadtesting/', include('loadtesting.urls')),
    )
    
urlpatterns += patterns('main.views',
    # the following pattern is a catch-all, so keep it last:
<<<<<<< HEAD
    url(r'^topics/(?P<splat>.+)/$', 'splat_handler', {}, 'splat_handler'),
=======
    url(r'^(?P<splat>.+)/$', 'splat_handler', {}, 'splat_handler'),
>>>>>>> origin/separate_server_code
)

handler404 = 'main.views.distributed_404_handler'
handler500 = 'main.views.distributed_500_handler'
