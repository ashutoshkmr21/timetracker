from django.conf.urls import patterns, url, include

from django.views.generic import TemplateView

from userinfo import views
urlpatterns = patterns('',
                       url(r'^login/$', 'django.contrib.auth.views.login',name='login'),
                       url(r'^main/$', views.DashBoard.as_view(), name="main_page"),
                       url(r'^send_mail/(?P<pk>\d+)/$', views.SendMail.as_view(), name="send_mail"),
                       url(r'^send_response_mail/(?P<pk>\d+)/$', views.SendResponseMail.as_view(), name="send_response_mail"),
                       url(r'^logout/$', views.SignOut.as_view(), name="logout"),
                       url(r'^register/$', views.register_page.as_view(), name='register'),
                       url(r'^org_members/$', views.OrgMembersList.as_view(), name="org_members"),
                       url(r'^team_members/$', views.TeamMembersList.as_view(), name="team_members"),
                       url(r'^register/success/$', TemplateView.as_view(template_name='registration/register_success.html'), name="register_success"),

)


