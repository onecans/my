from django import forms
from .models import *
from .models import *

class ReportImportForm(forms.Form):
    report = forms.ModelChoiceField(queryset=Report.objects.all())
    data = forms.CharField(widget=forms.Textarea(attrs={'rows':20,'cols':80}))
    amount_re = forms.CharField(initial='(~[+-]{0,1}[0-9]{1,3}(,[0-9]{3})*)')
    item_re = forms.CharField(initial='''([\\u4e00-\\u9fa5\(\)“\-”/]+)~''')


class GroupReportForm(forms.Form):
    group = forms.ModelChoiceField(queryset=Group.objects.all(), initial='铝')
    year = forms.IntegerField(max_value=3000, initial='2017')
    # report_type = forms.ChoiceField(choices=Report.REPORT_TYPE_CHOICES, initial=Report.HALF_YEAR_TYPE)
    report_name = forms.ChoiceField(choices=Report.REPORT_NAME_CHOICES,  initial='资产负债表')


class FormulaReportForm(forms.Form):
    report = forms.ModelChoiceField(queryset=Report.objects.all(), required=False)
