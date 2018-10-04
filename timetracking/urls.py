from django.conf.urls import patterns, url
from timetracking import views
urlpatterns = patterns('',
                       url(r'^edit_timesheet/(?P<pk>\d+)/$', views.TimeSheetEdit.as_view(),name='edit_timesheet'),
                       url(r'^timesheet_status/$', views.TimeSheetStatus.as_view(),name='timesheet_status'),
                       url(r'^timesheet_submission_request/$', views.TimeSheetSubmissionRequest.as_view(), name="submission_request"),
                       url(r'^bar_view/$', views.BarView.as_view(),name='bar_view'),
                       url(r'^graph_view/$', views.GraphView.as_view(),name='graph_view'),
                       url(r'^graphical_analysis/$', views.GraphicalAnalysis.as_view(),name='graphical_analysis'),
                       url(r'^csv_download/$', views.DataView.as_view(),name='csv_download'),
)

