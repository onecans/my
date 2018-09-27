from django import forms
from .models import *
class ReportHandlerForm(forms.Form):
    pass
    # stock = forms.ModelChoiceField(queryset=Stock.objects.all())
    # url = forms.URLField()
    # pass

class GroupReportForm(forms.Form):
    group = forms.ModelChoiceField(queryset=Group.objects.all(), initial='铝')
    period = forms.CharField(max_length=11, initial='2017-06-30')
    # report_type = forms.ChoiceField(choices=Report.REPORT_TYPE_CHOICES, initial=Report.HALF_YEAR_TYPE)
    # report_name = forms.ChoiceField(choices=Report.REPORT_NAME_CHOICES,  initial='资产负债表')

    