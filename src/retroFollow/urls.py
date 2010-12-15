from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^b/(\S+)/$', 'retroFollow.views.old_user_timeline'),
    (r'^(\S+)/$', 'retroFollow.views.user_timeline'),
)
