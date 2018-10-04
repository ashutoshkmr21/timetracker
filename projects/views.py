import random
from django.views.generic import CreateView,UpdateView, ListView
from django.views.generic.base import TemplateView
from projects.models import ProjectAssignment,ActivityLog
from projects.forms import *
from django.core.urlresolvers import reverse
from timetracking.models import TimeSheetData
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from highcharts.views import HighChartsBarView

class CreateProject(CreateView):

    model = Project
    template_name = 'ProjectCreateForm.html'
    form_class = ProjectForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(CreateProject, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateProject, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()

        for obj in form.cleaned_data['Assigned_to']:
            project_assignement = ProjectAssignment(project=self.object, assigned_to=obj )
            project_assignement.save()

            for NewObj in form.cleaned_data['Admin(s)']:

                if NewObj == obj:
                    project_assignement.admin_flag = True
                    project_assignement.save()

        return super(CreateProject, self).form_valid(form)

    def get_success_url(self):
        return reverse('main_page')

    def get_context_data(self, **kwargs):
        user = User.objects.get(username= self.request.user.username)
        context = super(CreateProject, self).get_context_data(**kwargs)
        context['team_admin'] = ""
        context['org_admin'] = ""
        context['project_assigned'] = ProjectAssignment.objects.filter(assigned_to=self.request.user.id)

        if ProjectAssignment.objects.filter(assigned_to=user.id, admin_flag=True):
            context['team_admin'] = "True"

        if user.user_type == 1:
            context['org_admin'] = "True"

        return context


class EditProject(UpdateView):

    model = Project
    template_name = 'ProjectCreateForm.html'
    form_class = ProjectForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(EditProject, self).dispatch(request,*args, **kwargs)

    def get_initial(self):
        assigned = ProjectAssignment.objects.filter(project=self.object).values_list('assigned_to', flat=True)
        admin = ProjectAssignment.objects.filter(project=self.object, admin_flag=True).values_list('assigned_to',
                                                                                                   flat=True)
        return {'Assigned_to': assigned,'Admin(s)': admin}

    def get_form_kwargs(self):
        kwargs = super(EditProject, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        assigned = ProjectAssignment.objects.filter(project=self.object)

        for obj in assigned:
            obj.delete()

        for obj in form.cleaned_data['Assigned_to']:
            project_assignement = ProjectAssignment(project=self.object, assigned_to=obj )
            project_assignement.save()

            for NewObj in form.cleaned_data['Admin(s)']:

                if NewObj == obj:
                    project_assignement.admin_flag = True
                    project_assignement.save()

        return super(EditProject, self).form_valid(form)

    def get_success_url(self):
        return reverse('project-list')

    def get_context_data(self, **kwargs):

        context = super(EditProject, self).get_context_data(**kwargs)
        context['action'] = reverse('edit-project', kwargs={'pk': self.get_object().id})
        user = User.objects.get(username=self.request.user.username)
        context['team_admin'] = ""
        context['org_admin'] = ""
        context['timesheet_flag'] = ""

        if TimeSheetData.objects.filter(user=self.request.user):
            context['timesheet_flag'] = True

        context['project_assigned'] = ProjectAssignment.objects.filter(assigned_to=self.request.user.id)

        if ProjectAssignment.objects.filter(assigned_to=user.id, admin_flag=True):
            context['team_admin'] = "True"

        if user.user_type == 1:
            context['org_admin'] = "True"

        return context


class ProjectList(ListView):

    model = Project
    template_name = 'project_list.html'
    paginate_by = 3

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ProjectList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        self.queryset = Project.objects.filter(status=0)
        return super(ProjectList,self).get_queryset()


    def get_context_data(self, **kwargs):
        user = User.objects.get(username=self.request.user.username)
        context = super(ProjectList, self).get_context_data(**kwargs)
        #context['object_list'] = Project.objects.filter(status=0)
        context['team_admin'] = ""
        context['org_admin'] = ""
        context['timesheet_flag'] = ""

        if TimeSheetData.objects.filter(user=self.request.user):
            context['timesheet_flag'] = True

        context['project_assigned'] = ProjectAssignment.objects.filter(assigned_to=self.request.user.id)

        if ProjectAssignment.objects.filter(assigned_to=user.id, admin_flag=True):
            context['team_admin'] = "True"

        if user.user_type == 1:
            context['org_admin'] = "True"

        return context

class ActivityList(ListView):
    model = ActivityLog
    template_name = 'activity_list.html'
    paginate_by = 8

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ActivityList, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user = User.objects.get(username=self.request.user.username)
        context = super(ActivityList, self).get_context_data(**kwargs)
        context['team_admin'] = ""
        context['org_admin'] = ""
        context['timesheet_flag'] = ""
        context['users'] = User.objects.all()
        context['projects'] = Project.objects.all()

        if TimeSheetData.objects.filter(user=self.request.user):
            context['timesheet_flag'] = True

        context['project_assigned'] = ProjectAssignment.objects.filter(assigned_to=self.request.user.id)

        if ProjectAssignment.objects.filter(assigned_to=user.id, admin_flag=True):
            context['team_admin'] = "True"

        if user.user_type == 1:
            context['org_admin'] = "True"
        return context

# Create your views here.