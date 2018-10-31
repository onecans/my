from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^stock/report_handler/(?P<code>[0-9]+)', views.report_handler_view, name='report_handler'),
    url(r'^stock/group_report/', views.GroupReportView.as_view(), name='group_report'),
    url(r'^stock/dfs', views.DfsView.as_view(), name='dfs')
    
]
