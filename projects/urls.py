from django.conf.urls import patterns, url, include

from django.views.generic import TemplateView

from projects import views
urlpatterns = patterns('',
                       url(r'^create_project/$', views.CreateProject.as_view(), name='createProject'),
                       url(r'^edit_project/(?P<pk>\d+)/$', views.EditProject.as_view(), name='edit-project'),
                       url(r'^projects_list/$', views.ProjectList.as_view(), name='project-list'),
                       url(r'^activity_list/$', views.ActivityList.as_view(), name='activity_list'),


              )


