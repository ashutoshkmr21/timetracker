from datetime import timedelta, datetime
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models.query_utils import Q
from django.http.response import Http404
from django.shortcuts import render
from django.views.generic.base import RedirectView, TemplateView
from django.contrib.auth import logout
from django.views.generic.list import ListView
from forms import *
from django.http import HttpResponseRedirect
from django.views.generic import View
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from projects.models import Project,ProjectAssignment
from timetracking.models import TimeSheetWeekData,TimeSheetData
from django.db import connection
from django.template.loader import get_template
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Context
User = get_user_model()


class DashBoard(TemplateView):

    template_name = 'member_page.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(DashBoard, self).dispatch(request, *args, **kwargs)


    #def get_template_names(self):
    #    return ['member_page.html']

    def get_context_data(self, **kwargs):
        user = User.objects.get(username=self.request.user.username)
        pk = user.id
        context = super(DashBoard, self).get_context_data(**kwargs)
        cursor = connection.cursor()
        cursor.execute("SELECT EXTRACT(WEEK FROM tw.date) AS regweek,date_trunc('week',tw.date),SUM(tw.time_spent) FROM timetracking_timesheetweekdata tw INNER JOIN timetracking_timesheetdata td ON tw.timesheet_id = td.id  where td.user_id = %s  GROUP BY regweek,date_trunc('week',tw.date) ORDER BY regweek ",[pk])
        results = cursor.fetchall()
        total_time = []
        for result in results:
            start_date = result[1]
            end_date = start_date+timedelta(days = 6)
            start_date = start_date.strftime('%m/%d/%Y')
            end_date = end_date.strftime('%m/%d/%Y')
            time_list = {'week': '', 'time': '', 'start_date': '', 'end_date': ''}
            time_list['week'] = int(result[0]) - 1
            time_list['start_date'] = start_date
            time_list['end_date'] = end_date
            time_list['time'] = int(result[2])
            total_time.append(time_list)

        context['results'] = total_time
        cursor.execute("SELECT td.user_id,EXTRACT(WEEK FROM tw.date) AS regweek,date_trunc('week',tw.date),SUM(tw.time_spent) FROM timetracking_timesheetweekdata tw INNER JOIN timetracking_timesheetdata td ON tw.timesheet_id = td.id  GROUP BY td.user_id,regweek,date_trunc('week',tw.date) ORDER BY regweek ")
        users_week_time = cursor.fetchall()
        total_time_user = []

        for result in users_week_time:
            start_date = result[2]
            end_date = start_date+timedelta(days=6)
            start_date = start_date.strftime('%m/%d/%Y')
            end_date = end_date.strftime('%m/%d/%Y')
            time_list = {'id': '', 'week': '', 'time': '', 'start_date': '', 'end_date': ''}
            time_list['id'] = int(result[0])
            time_list['week'] = int(result[1]) - 1
            time_list['start_date'] = start_date
            time_list['end_date'] = end_date
            time_list['time'] = int(result[3])
            total_time_user.append(time_list)

        user = User.objects.get(username= self.request.user.username)
        project = Project.objects.filter(projectassignment__assigned_to=user, projectassignment__admin_flag=True)
        team_members = User.objects.filter(projectassignment__project=project, projectassignment__admin_flag=False)
        context['timesheet_flag'] = ""
        if TimeSheetData.objects.filter(user=self.request.user):
            context['timesheet_flag'] = True
        context['team_admin'] = ""
        context['org_admin'] = ""
        context['project_assigned'] = ProjectAssignment.objects.filter(assigned_to=self.request.user.id)
        if ProjectAssignment.objects.filter(assigned_to=user.id, admin_flag=True):
            context['team_admin'] = "True"
            context['users_week_time'] = total_time_user
            context['team_members'] = team_members
            context['members'] = User.objects.filter(projectassignment__project=project,
                                                     projectassignment__admin_flag=False).distinct()
            context['projects'] = project
        if user.user_type == 1:
            context['org_admin'] = "True"
            context['users_week_time'] = total_time_user
            context['all_members'] = User.objects.filter(~Q(id=self.request.user.id))
            context['members'] = User.objects.filter(~Q(id=self.request.user.id))
            context['projects'] = Project.objects.all()
        if TimeSheetData.objects.filter(user=user):
            timesheet = TimeSheetData.objects.filter(user=user)
            context['timesheet'] = timesheet
            context['weekdata'] = TimeSheetWeekData.objects.filter(timesheet__user=user).order_by('date')
        return context


class SignOut(RedirectView):

    def get_redirect_url(self):
        logout(self.request)
        return reverse('login')


class OrgMembersList(ListView):
    model = User
    template_name = 'org_members_list.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(OrgMembersList, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user = User.objects.get(username=self.request.user.username)
        if user.user_type != 1:
            raise Http404('Page Not Found')
        context = super(OrgMembersList, self).get_context_data(**kwargs)
        today = datetime.now()
        today = today.strftime('%m/%d/%Y')
        context['today'] = today
        context['timesheet_flag'] = ""
        if TimeSheetData.objects.filter(user=self.request.user):
            context['timesheet_flag'] = True
        context['team_admin'] = ""
        context['org_admin'] = ""
        context['project_assigned'] = ProjectAssignment.objects.filter(assigned_to=self.request.user.id)
        if ProjectAssignment.objects.filter(assigned_to=user.id, admin_flag=True):
            context['team_admin'] = "True"
        if user.user_type == 1:
            context['org_admin'] = "True"
        context['current_user'] = user
        return context

class TeamMembersList(TemplateView):

    template_name = 'team_members_list.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TeamMembersList, self).dispatch(request, *args, **kwargs)


    #def get_template_names(self):
    #    return ['team_members_list.html']

    def get_context_data(self, **kwargs):
        user = User.objects.get(username= self.request.user.username)
        #projects = ProjectAssignment.objects.all()
        project_objs = Project.objects.filter(projectassignment__assigned_to=user, projectassignment__admin_flag=True)
        print project_objs.query
        #team_members = User.objects.filter(projectassignment__project = project_objs).distinct()
        project_assigned_team_member = ProjectAssignment.objects.select_related().filter(project__in=project_objs).distinct().order_by('project')
        dummy_query = ProjectAssignment.objects.select_related().filter(project__projectassignment__assigned_to=user,
                                                                        project__projectassignment__admin_flag=True)
        print 'dummmmyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy'
        print dummy_query.query
        for d in dummy_query:
            print d.project.project_name,d.assigned_to.username

        context = super(TeamMembersList, self).get_context_data(**kwargs)
        today = datetime.now()
        today = today.strftime('%m/%d/%Y')
        context['today'] = today
        #context['projects'] = projects
        context['project_objs'] = project_objs
        context['team_member'] = project_assigned_team_member
        #context['team_members'] = team_members
        context['team_admin'] = ""
        context['org_admin'] = ""
        context['timesheet_flag']=""
        if TimeSheetData.objects.filter(user=self.request.user):
            context['timesheet_flag'] = True
        context['current_user'] = user
        if ProjectAssignment.objects.filter(assigned_to=user.id, admin_flag=True):
            context['team_admin'] = "True"
        if user.user_type == 1:
            context['org_admin'] = "True"
        context['current_user'] = user
        return context



class SendMail(TemplateView):

    template_name = 'mail_sent.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(SendMail, self).dispatch(request, *args, **kwargs)

    #def get_template_names(self):
    #    return ['mail_sent.html']

    def get(self, request, *args, **kwargs):
        start_date = request.GET['date']
        start_date = datetime.strptime(start_date, '%m/%d/%Y')
        start_date = start_date - timedelta(days=start_date.weekday())
        end_date = start_date+timedelta(days=6)
        user = User.objects.get(id=self.kwargs['pk'])
        timesheets = TimeSheetData.objects.filter(user=user,
                                                  timesheetweekdata__date__range=[start_date, end_date]).distinct()
        #test_query = TimeSheetWeekData.objects.select_related().filter()

        if not timesheets:
            context = self.get_context_data()
            context['mail'] = ""
            return render(request, self.get_template_names(), context)

        projects = timesheets.filter(user=user).values('project').distinct()
        admin_list = []

        for project in projects:
            users = User.objects.filter(projectassignment__project_id=project['project'],
                                        projectassignment__admin_flag=True)
            for user in users:
                if user.username not in admin_list:
                    if user == self.request.user:
                        for each_user in User.objects.all():
                            if each_user.user_type == 1 and each_user.username not in admin_list:
                                admin_list.append(each_user.username)
                    else:
                        admin_list.append(user.username)

        for list in admin_list:
            current_user = User.objects.get(username=list)
            subject = u'Submission of Timesheet'
            link = 'http://localhost:8000/timetracking/timesheet_submission_request/?sent_to=%s&sent_from=%s&date=%s' % (current_user.id,self.request.user.id,start_date)
            plaintext = get_template('submission_email.txt')
            htmltext = get_template('submission_email.html')
            context = Context({'name': list,'link': link,'sender': self.request.user.username})
            from_email = settings.DEFAULT_FROM_EMAIL
            to = current_user.email
            text_content = plaintext.render(context)
            html_content = htmltext.render(context)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()

        context = self.get_context_data()
        context['mail'] = True
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        user = User.objects.get(username = self.request.user.username)
        context = super(SendMail, self).get_context_data(**kwargs)
        context['team_admin'] = ""
        context['org_admin'] = ""
        context['timesheet_flag'] = ""
        if TimeSheetData.objects.filter(user=self.request.user):
            context['timesheet_flag'] = True
        context['current_user'] = user
        if ProjectAssignment.objects.filter(assigned_to=user.id, admin_flag=True):
            context['team_admin'] = "True"
        if user.user_type == 1:
            context['org_admin'] = "True"
        context['current_user'] = user
        return context


class SendResponseMail(TemplateView):

    template_name = 'mail_sent.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(SendResponseMail, self).dispatch(request, *args, **kwargs)


    #def get_template_names(self):
    #    return ['mail_sent.html']

    def get(self, request, *args, **kwargs):

        if 'rejection_message' in request.GET:
            message = request.GET['rejection_message']
            user = User.objects.get(id= request.GET['id'])
            subject = u'Response of Submitted Timesheet'
            plaintext = get_template('submission_rejected.txt')
            htmltext = get_template('submission_rejected.html')
            context = Context({'name': user.username, 'message': message, 'sender': self.request.user.username})
            from_email = settings.DEFAULT_FROM_EMAIL
            to = user.email
            text_content = plaintext.render(context)
            html_content = htmltext.render(context)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            context = self.get_context_data()
            context['mail'] = "True"
            return render(request, self.template_name, context)

        start_date = request.GET['date']
        start_date = datetime.strptime(start_date, '%m/%d/%Y')
        start_date = start_date - timedelta(days=start_date.weekday())
        end_date = start_date+timedelta(days=6)
        user = User.objects.get(id=request.GET['id'])
        timesheets = TimeSheetData.objects.filter(user=user,
                                                  timesheetweekdata__date__range=[start_date, end_date]).distinct()

        if request.user.user_type != 1:
            for timesheet in timesheets:
                if ProjectAssignment.objects.filter(project_id=timesheet.project_id, assigned_to=request.user,
                                                    admin_flag=True).exists():
                    timesheet.status = 2
                    timesheet.save()

        else:
            for timesheet in timesheets:
                timesheet.status = 2
                timesheet.save()

        subject = u'Response of Submitted Timesheet'
        plaintext = get_template('submission_review.txt')
        htmltext = get_template('submission_review.html')
        context = Context({'name': user.username,'sender': self.request.user.username})
        from_email = settings.DEFAULT_FROM_EMAIL
        to = user.email
        text_content = plaintext.render(context)
        html_content = htmltext.render(context)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        context = self.get_context_data()
        context['mail'] = "True"
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        user = User.objects.get(username = self.request.user.username)
        context = super(SendResponseMail, self).get_context_data(**kwargs)
        context['team_admin'] = ""
        context['org_admin'] = ""
        context['timesheet_flag'] = ""
        if TimeSheetData.objects.filter(user=self.request.user):
            context['timesheet_flag'] = True
        context['current_user'] = user
        if ProjectAssignment.objects.filter(assigned_to=user.id, admin_flag=True):
            context['team_admin'] = "True"
        if user.user_type == 1:
            context['org_admin'] = "True"
        context['current_user'] = user
        return context


class register_page(View):
    form_class = RegistrationForm
    initial = {'key': 'value'}
    template_name = 'registration/register.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = User.objects.create_user(username=form.cleaned_data['username'],password=form.cleaned_data['password1'],email=form.cleaned_data['email'])
            return HttpResponseRedirect('/userinfo/register/success/')
        return render(request, self.template_name, {'form': form})
# Create your views here.