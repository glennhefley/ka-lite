from django.http import HttpResponseRedirect
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

import securesync.urls
from kalite import settings

def redirect_to(self, base_url, path=""):
    return HttpResponseRedirect(base_url + path)
    
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^securesync/', include(securesync.urls)),
)

urlpatterns += patterns('',
    url(r'^' + settings.STATIC_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.STATIC_ROOT,
    }),
    url(r'^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_URL,
    }),
    url(r'^' + settings.CONTENT_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.CONTENT_ROOT,
    }),
)
        
# Javascript translations
urlpatterns += patterns('',
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('ka-lite.locale')}, 'i18n_javascript_catalog'),
)

from feeds import RssSiteNewsFeed, AtomSiteNewsFeed

urlpatterns += patterns('central.views',
    url(r'^$', 'landing_page', {}, 'landing_page'), 
    url(r'^delete_admin/(?P<org_id>\w+)/(?P<user_id>\w+)/$', 'delete_admin', {}, 'delete_admin'), 
    url(r'^delete_invite/(?P<org_id>\w+)/(?P<invite_id>\w+)/$', 'delete_invite', {}, 'delete_invite'), 
    url(r'^accounts/', include('registration.urls')),

    url(r'^organization/$', 'org_management', {}, 'org_management'),
    url(r'^organization/(?P<id>\w+)/$', 'organization_form', {}, 'organization_form'),
    url(r'^organization/(?P<org_id>\w+)/zone/(?P<zone_id>\w+)/edit$', 'zone_form', {}, 'zone_form'),
    url(r'^organization/(?P<org_id>\w+)/zone/(?P<zone_id>\w+)/$', 'zone_management', {}, 'zone_management'),
    url(r'^organization/(?P<org_id>\w+)/zone/(?P<zone_id>\w+)/device/(?P<device_id>\w+)/$', 'device_management', {}, 'device_management'),
    url(r'^organization/(?P<org_id>\w+)/zone/(?P<zone_id>\w+)/facility/$', 'facility_management', {}, 'facility_management'),
    url(r'^organization/(?P<org_id>\w+)/zone/(?P<zone_id>\w+)/facility/(?P<id>\w+)/edit$', 'facility_form', {}, 'facility_form'),
    url(r'^organization/(?P<org_id>\w+)/zone/(?P<zone_id>\w+)/facility/(?P<id>\w+)/mastery/$', 'facility_mastery', {}, 'facility_mastery'),
    url(r'^organization/(?P<org_id>\w+)/zone/(?P<zone_id>\w+)/facility/(?P<id>\w+)/usage/$', 'facility_usage', {}, 'facility_usage'),
    url(r'^organization/(?P<org_id>\w+)/zone/(?P<zone_id>\w+)/facility/(?P<id>\w+)/upload/$', 'facility_data_upload', {}, 'facility_data_upload'),
    url(r'^organization/(?P<org_id>\w+)/zone/(?P<zone_id>\w+)/facility/(?P<id>\w+)/download/$', 'facility_data_download', {}, 'facility_data_download'),
    url(r'^organization/invite_action/(?P<invite_id>\w+)/$', 'org_invite_action', {}, 'org_invite_action'),

    url(r'^cryptologin/$', 'crypto_login', {}, 'crypto_login'), 
#    url(r'^getstarted/$','get_started', {}, 'get_started'),
    url(r'^glossary/$', 'glossary', {}, 'glossary'),
    url(r'^addsubscription/$', 'add_subscription', {}, 'add_subscription'),
    url(r'^feeds/rss/$', RssSiteNewsFeed(), {}, 'rss_feed'),
    url(r'^feeds/atom/$', AtomSiteNewsFeed(), {}, 'atom_feed'),
    url(r'^faq/', include('faq.urls')),
    url(r'^contact/', include('contact.urls')),
    url(r'^install/$', 'install_wizard', {}, 'install_wizard'),

    url(r'^wiki/(?P<path>\w+)/$', redirect_to, {'base_url': settings.CENTRAL_WIKI_URL}),
    url(r'^about/$', redirect_to, { 'base_url': 'http://learningequality.org/' }),

    url(r'^download/kalite/(?P<args>.*)/$', 'download_kalite', {"argnames": ["platform", "locale", "zone_id", "n_certs"]}, 'download_kalite'),
)

handler404 = 'central.views.central_404_handler'
handler500 = 'central.views.central_500_handler'

