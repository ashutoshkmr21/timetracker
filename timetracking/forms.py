from django import forms
from models import TimeSheetData,TimeSheetWeekData
from projects.models import Project
from django.contrib.auth import get_user_model
User = get_user_model()


class TimeSheetForm(forms.ModelForm):
    mon = forms.IntegerField(max_value=9,min_value=0,initial=0)
    tue = forms.IntegerField(max_value=9,min_value=0,initial=0)
    wed = forms.IntegerField(max_value=9,min_value=0,initial=0)
    thu = forms.IntegerField(max_value=9,min_value=0,initial=0)
    fri = forms.IntegerField(max_value=9,min_value=0,initial=0)
    sat = forms.IntegerField(max_value=9,min_value=0,initial=0)
    sun = forms.IntegerField(max_value=9,min_value=0,initial=0)

    class Meta:
        model = TimeSheetData
        exclude = ('id','user','status')

    def __init__(self,user, *args, **kwargs):
        super(TimeSheetForm, self).__init__(*args, **kwargs)
        qs = Project.objects.filter(projectassignment__assigned_to=user).distinct()
        self.fields['project'].queryset = qs