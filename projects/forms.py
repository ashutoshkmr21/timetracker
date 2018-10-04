from django import forms
from django.db.models import Q
from projects.models import Project
from django.contrib.auth import get_user_model
User = get_user_model()

class ProjectForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.fields['Assigned_to'] = forms.ModelMultipleChoiceField(queryset=User.objects.filter(~Q(username=user)))
        self.fields['Admin(s)'] = forms.ModelMultipleChoiceField(queryset=User.objects.filter(~Q(username=user)))

    class Meta:
        model = Project


