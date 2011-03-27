from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^([a-zA-Z0-9_]+)/$', 'retroFollow.views.user_timeline'),
    (r'^([a-zA-Z0-9_]+)/(\d+)$', 'retroFollow.views.user_timeline'),
    url(r'^([a-zA-Z0-9_]+)/status/(\d+)$', 'retroFollow.views.single_tweet', name='rf_single_tweet'),
)
