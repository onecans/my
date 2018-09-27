from django import forms


class KSearchForm(forms.Form):
    start = forms.DateField()
    end = forms.DateField()
    code1 = forms.CharField(max_length=20)
    col1 = forms.CharField(max_length=20, initial='high')
    is_index1 = forms.BooleanField(initial=False, required=False)

    code2 = forms.CharField(max_length=20, initial='999999')
    col2 = forms.CharField(max_length=20, initial='high')
    is_index2 = forms.BooleanField(initial=False, required=False)
