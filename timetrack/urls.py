from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'timetrack.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^timetracking/', include('timetracking.urls')),
    url(r'^userinfo/', include('userinfo.urls')),
    url(r'^projects/', include('projects.urls')),
)
