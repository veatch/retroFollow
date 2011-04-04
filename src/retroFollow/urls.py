from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
handler404 = 'retroFollow.views.fourohfour'

urlpatterns = patterns('',
    (r'^$', 'retroFollow.views.front_page'),
    url(r'^login$', 'retroFollow.views.auth', name='login'),
    url(r'^login/callback$', 'retroFollow.views.callback', name='callback'),
    (r'^logout$', 'retroFollow.views.logout'),
    (r'^([a-zA-Z0-9_]+)/$', 'retroFollow.views.user_timeline'),
    (r'^([a-zA-Z0-9_]+)/(\d+)$', 'retroFollow.views.user_timeline'),
    url(r'^([a-zA-Z0-9_]+)/status/(\d+)$', 'retroFollow.views.single_tweet', name='rf_single_tweet'),
)
