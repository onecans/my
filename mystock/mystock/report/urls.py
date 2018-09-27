from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^report_import', views.ReportImportView.as_view(), name='report_import'),
    url(r'^group_report', views.group_report_view, name='group_report'),
    url(r'^formula_report', views.formula_report, name='formula_report')
]