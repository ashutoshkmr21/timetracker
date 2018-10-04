# Create your views here.
import json
import csv
from django.contrib.auth.decorators import login_required
from django.db.models.aggregates import Sum
from django.utils.decorators import method_decorator
from django.db.models.query_utils import Q
from highcharts.views.bar import HighChartsBarView
from timetracking.signals import *
from django.http.response import Http404, HttpResponse
from django.views.generic import View
from django.shortcuts import render
from django.views.generic.base import TemplateView
from projects.models import ProjectAssignment, Project
from functools import partial, wraps
from django.forms.formsets import formset_factory
from django.contrib.auth import get_user_model
from timetracking.forms import TimeSheetForm
from timetracking.models import TimeSheetData, TimeSheetWeekData
from datetime import datetime, timedelta
from django.db import connection
User = get_user_model()


class TimeSheetEdit(View):

    form_class = TimeSheetForm
    model = TimeSheetData
    template_name = 'timesheet_edit_form.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TimeSheetEdit, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        team_admin = ""
        org_admin = ""
        start_date = request.GET['date']
        start_date = datetime.strptime(start_date, '%m/%d/%Y')
        start_date = start_date - timedelta(days=start_date.weekday())
        end_date = start_date+timedelta(days=6)
        next_week = start_date+timedelta(days=7)
        next_week = next_week.strftime('%m/%d/%Y')
        previous_week = start_date+timedelta(days=-6)
        previous_week = previous_week.strftime('%m/%d/%Y')
        s_date = start_date.strftime('%m/%d/%Y')
        e_date = end_date.strftime('%m/%d/%Y')
        requested_user = User.objects.get(id=self.kwargs['pk'])
        team_admin = ProjectAssignment.objects.filter(assigned_to=self.request.user, admin_flag=True).values_list(
            'project', flat=True)
        if request.user.user_type != 1:
            if not team_admin and requested_user != request.user:
                raise Http404('Page Not Found')

        members = ProjectAssignment.objects.filter(project=team_admin).values_list('assigned_to', flat=True).distinct()

        if request.user.user_type != 1:
            if requested_user.id not in members and requested_user != request.user:
                raise Http404('Page Not Found')

        timesheets = TimeSheetData.objects.filter(user=requested_user,timesheetweekdata__date__range=
        [start_date, end_date]).distinct()
        week_time_spent_edit = []
        week_time_spent_nonedit = []

        for timesheet in timesheets:
            count = 1
            initial_timesheet_data = {'status': '', 'project': '', 'issue_id': '', 'issue_description': '', 'mon': '',
                                      'tue': '', 'wed': '', 'thu': '', 'fri': '', 'sat': '', 'sun': ''}
            weekdata = TimeSheetWeekData.objects.filter(timesheet=timesheet).order_by('date')
            initial_timesheet_data['status']=timesheet.status
            #for editable if condition true else non-editable

            if timesheet.status == 0 and requested_user == self.request.user:
                initial_timesheet_data['project'] = timesheet.project_id
            else:
                obj = Project.objects.get(id=timesheet.project_id)
                initial_timesheet_data['project'] = obj.project_name

            initial_timesheet_data['issue_id'] = timesheet.issue_id
            initial_timesheet_data['issue_description'] = timesheet.issue_description

            for data in weekdata:
                if count == 1:
                    initial_timesheet_data['mon'] = data.time_spent
                elif count == 2:
                    initial_timesheet_data['tue'] = data.time_spent
                elif count == 3:
                    initial_timesheet_data['wed'] = data.time_spent
                elif count == 4:
                    initial_timesheet_data['thu'] = data.time_spent
                elif count == 5:
                    initial_timesheet_data['fri'] = data.time_spent
                elif count == 6:
                    initial_timesheet_data['sat'] = data.time_spent
                elif count == 7:
                    initial_timesheet_data['sun'] = data.time_spent
                count += 1

            if timesheet.status == 0 and requested_user == self.request.user:
                week_time_spent_edit.append(initial_timesheet_data)
            else:
                week_time_spent_nonedit.append(initial_timesheet_data)

        try:
            if request.GET['current_date']:
                copy_from = request.GET['current_date']
                copy_from = datetime.strptime(copy_from, '%m/%d/%Y')
                copy_from = copy_from - timedelta(days=copy_from.weekday())
                copy_to = copy_from+timedelta(days=6)
                timesheets = TimeSheetData.objects.filter(user=requested_user,
                                                          timesheetweekdata__date__range=[copy_from,copy_to]).distinct()

                for timesheet in timesheets:
                    initial_timesheet_data = {'status': '', 'project': '', 'issue_id': '', 'issue_description': '',
                                              'mon': '', 'tue': '', 'wed': '', 'thu': '', 'fri':'', 'sat': '', 'sun': ''}
                    initial_timesheet_data['status'] = timesheet.status
                    #for editable if condition true else non-editable
                    initial_timesheet_data['project'] = timesheet.project_id
                    initial_timesheet_data['issue_id'] = timesheet.issue_id
                    initial_timesheet_data['issue_description'] = timesheet.issue_description
                    initial_timesheet_data['mon'] = 0
                    initial_timesheet_data['tue'] = 0
                    initial_timesheet_data['wed'] = 0
                    initial_timesheet_data['thu'] = 0
                    initial_timesheet_data['fri'] = 0
                    initial_timesheet_data['sat'] = 0
                    initial_timesheet_data['sun'] = 0
                    week_time_spent_edit.append(initial_timesheet_data)
        except:
            pass

        edit_flag = ""
        member_flag = ""

        if week_time_spent_edit:
            edit_flag = "True"

        if requested_user != self.request.user:
            edit_flag = ""
        TimeSheetFormSet = formset_factory(wraps(TimeSheetForm)(partial(TimeSheetForm, user=self.request.user)),
                                           extra=1, can_delete=True)

        if timesheets:
            formset = TimeSheetFormSet(initial=week_time_spent_edit )
        else:
            if requested_user == self.request.user:
                edit_flag = "True"
            else:
                edit_flag = ""
                member_flag = "True"
            formset = TimeSheetFormSet()
        requested_user_flag = ""

        if requested_user != self.request.user and (not timesheets):
            requested_user_flag = ""

        timesheet_flag = ""

        if TimeSheetData.objects.filter(user=self.request.user):
            timesheet_flag = True

        if timesheets and self.request.user.user_type == 1:
            requested_user_flag = "True"

        if ProjectAssignment.objects.filter(assigned_to=self.request.user.id, admin_flag="True"):
            team_admin = "True"

        if self.request.user.user_type == 1:
            org_admin = "True"

        return render(request, self.template_name, {'formset': formset,
                                                    'project_assigned': ProjectAssignment.objects.filter(assigned_to=
                                                    self.request.user), 'team_admin':team_admin, 'org_admin':  org_admin,
                                                    'week_time_spent_nonedit': week_time_spent_nonedit,
                                                    'edit_flag': edit_flag, 'next_week':next_week,
                                                    'previous_week': previous_week, 's_date': s_date, 'e_date': e_date,
                                                    'requested_user': requested_user.id,
                                                    'requested_flag': requested_user_flag,
                                                    'timesheet_flag': timesheet_flag, 'member_flag': member_flag})

    def post(self, request, *args, **kwargs):
        team_admin = ""
        org_admin = ""
        start_date = request.POST.get('date')
        start_date = datetime.strptime(start_date, '%m/%d/%Y')
        start_date = start_date - timedelta(days=start_date.weekday())
        end_date = start_date+timedelta(days=6)
        next_week = start_date+timedelta(days=7)
        next_week = next_week.strftime('%m/%d/%Y')
        previous_week = start_date+timedelta(days=-6)
        previous_week = previous_week.strftime('%m/%d/%Y')
        s_date = start_date.strftime('%m/%d/%Y')
        e_date = end_date.strftime('%m/%d/%Y')
        requested_user = User.objects.get(id=self.kwargs['pk'])
        TimeSheetFormSet = formset_factory(wraps(TimeSheetForm)(partial(TimeSheetForm, user=self.request.user)),
                                           extra=1, can_delete=True)
        formset = TimeSheetFormSet(request.POST)
        formset.is_valid()

        for form in formset:
            form.is_valid()
            form = form.cleaned_data

            if form.get('DELETE'):
                project = Project.objects.none()

                if form.get('project'):
                    project = Project.objects.get(project_name=form.get('project'))

                issue_id = form.get('issue_id')
                description = form.get('issue_description')

                if not (project and issue_id and description):
                    continue

                timesheet_object = TimeSheetData.objects.get(project=project, issue_id=issue_id,
                                                             issue_description=description, user=request.user)
                weekdataobjects = TimeSheetWeekData.objects.filter(timesheet_id=timesheet_object.id).order_by('date')

                for wdobject in weekdataobjects:
                    wdobject.delete()

                timesheet_object.delete()

            if not form.get('DELETE'):
                project = Project.objects.none()

                if form.get('project'):
                    project = Project.objects.get(project_name=form.get('project'))

                issue_id = form.get('issue_id')
                description = form.get('issue_description')
                mon = 0
                tue = 0
                wed = 0
                thu = 0
                fri = 0
                sat = 0
                sun = 0

                if form.get('mon'):
                    mon = form.get('mon')

                if form.get('tue'):
                    tue = form.get('tue')

                if form.get('wed'):
                    wed = form.get('wed')

                if form.get('thu'):
                    thu = form.get('thu')

                if form.get('fri'):
                    fri = form.get('fri')

                if form.get('sat'):
                    sat = form.get('sat')

                if form.get('sun'):
                    sun = form.get('sun')

                    #issue already exist in timesheet
                if not (project and issue_id and description):
                    continue

                try:

                    if(TimeSheetData.objects.get(project=project, issue_id=issue_id, issue_description=description,
                                                 user=request.user)):
                        timesheet_object = TimeSheetData.objects.get(project=project, issue_id=issue_id,
                                                                     issue_description=description, user=request.user)
                        weekdataobjects = TimeSheetWeekData.objects.filter(timesheet_id=timesheet_object.id).order_by('date')
                        count = 1
                        update_flag = 0

                        for wdobject in weekdataobjects:

                            if count == 1:
                                if mon != wdobject.time_spent:
                                    update_flag = 1
                                wdobject.time_spent = mon
                                wdobject.save()

                            elif count == 2:
                                if tue != wdobject.time_spent:
                                    update_flag = 1
                                wdobject.time_spent = tue
                                wdobject.save()

                            elif count == 3:
                                if wed != wdobject.time_spent:
                                    update_flag = 1
                                wdobject.time_spent = wed
                                wdobject.save()

                            elif count == 4:
                                if thu != wdobject.time_spent:
                                    update_flag = 1
                                wdobject.time_spent = thu
                                wdobject.save()

                            elif count == 5:
                                if fri != wdobject.time_spent:
                                    update_flag = 1
                                wdobject.time_spent = fri
                                wdobject.save()

                            elif count == 6:
                                if sat != wdobject.time_spent:
                                    update_flag = 1
                                wdobject.time_spent = sat
                                wdobject.save()

                            elif count == 7:
                                if sun != wdobject.time_spent:
                                    update_flag=1
                                wdobject.time_spent = sun
                                wdobject.save()

                            count += 1

                        if update_flag == 1:
                            timesheet_signal.send(sender=TimeSheetData, user=timesheet_object.user,
                                                  project=timesheet_object.project)

                except TimeSheetData.DoesNotExist:
                    day = start_date
                    day = day.strftime('%d/%b/%Y')
                    dt = datetime.strptime(day, '%d/%b/%Y')
                    day = dt - timedelta(days=dt.weekday())
                    timesheet_object = TimeSheetData(user=self.request.user, project=project, issue_id=issue_id,
                                                     issue_description=description, status=0)
                    timesheet_object.save()
                    for count in range(1, 8, 1):
                        wdobject = TimeSheetWeekData(timesheet=timesheet_object)
                        if count == 1:
                            wdobject.time_spent = mon
                            wdobject.date = day
                            wdobject.save()
                        elif count == 2:
                            wdobject.time_spent = tue
                            wdobject.date = day + timedelta(days=1)
                            wdobject.save()
                        elif count == 3:
                            wdobject.time_spent = wed
                            wdobject.date = day + timedelta(days=2)
                            wdobject.save()
                        elif count == 4:
                            wdobject.time_spent = thu
                            wdobject.date = day + timedelta(days=3)
                            wdobject.save()
                        elif count == 5:
                            wdobject.time_spent = fri
                            wdobject.date = day + timedelta(days=4)
                            wdobject.save()
                        elif count == 6:
                            wdobject.time_spent = sat
                            wdobject.date = day + timedelta(days=5)
                            wdobject.save()
                        elif count == 7:
                            wdobject.time_spent = sun
                            wdobject.date = day + timedelta(days=6)
                            wdobject.save()
                        count += 1

        timesheets = TimeSheetData.objects.filter(user=requested_user,
                                                  timesheetweekdata__date__range=[start_date, end_date]).distinct()
        week_time_spent_edit = []
        week_time_spent_nonedit = []

        for timesheet in timesheets:
            count = 1
            initial_timesheet_data = {'status': '', 'project': '', 'issue_id': '', 'issue_description': '', 'mon': '',
                                      'tue': '', 'wed': '', 'thu': '', 'fri': '', 'sat': '', 'sun': ''}
            weekdata = TimeSheetWeekData.objects.filter(timesheet=timesheet).order_by('date')
            initial_timesheet_data['status'] = timesheet.status

            if timesheet.status == 0 and requested_user == self.request.user :
                initial_timesheet_data['project'] = timesheet.project_id
            else:
                obj = Project.objects.get(id=timesheet.project_id)
                initial_timesheet_data['project'] = obj.project_name

            initial_timesheet_data['issue_id'] = timesheet.issue_id
            initial_timesheet_data['issue_description'] = timesheet.issue_description

            for data in weekdata:
                if count == 1:
                    initial_timesheet_data['mon'] = data.time_spent
                elif count == 2:
                    initial_timesheet_data['tue'] = data.time_spent
                elif count == 3:
                    initial_timesheet_data['wed'] = data.time_spent
                elif count == 4:
                    initial_timesheet_data['thu'] = data.time_spent
                elif count == 5:
                    initial_timesheet_data['fri'] = data.time_spent
                elif count == 6:
                    initial_timesheet_data['sat'] = data.time_spent
                elif count == 7:
                    initial_timesheet_data['sun'] = data.time_spent
                count += 1

            if timesheet.status == 0 and requested_user == self.request.user:
                week_time_spent_edit.append(initial_timesheet_data)
            else:
                week_time_spent_nonedit.append(initial_timesheet_data)

        edit_flag = ""
        member_flag = ""

        if week_time_spent_edit:
            edit_flag = "True"

        if requested_user != self.request.user:
            edit_flag = ""
        TimeSheetFormSet = formset_factory(wraps(TimeSheetForm)(partial(TimeSheetForm, user=self.request.user)),
                                           extra=1, can_delete=True)

        if timesheets:
            formset = TimeSheetFormSet(initial=week_time_spent_edit )
        else:

            if requested_user == self.request.user:
                edit_flag = "True"
            else:
                edit_flag = ""
                member_flag = "True"
            formset = TimeSheetFormSet()
        requested_user_flag = ""

        if requested_user != self.request.user and (not timesheets):
            requested_user_flag = ""

        if timesheets and self.request.user.user_type == 1:
            requested_user_flag = "True"

        timesheet_flag = ""

        if TimeSheetData.objects.filter(user=self.request.user):
            timesheet_flag = True

        if ProjectAssignment.objects.filter(assigned_to=self.request.user.id, admin_flag=True):
            team_admin = "True"

        if self.request.user.user_type == 1:
            org_admin = "True"

        return render(request, self.template_name, {'formset': formset,
                                                    'project_assigned': ProjectAssignment.objects.filter(assigned_to=
                                                    self.request.user), 'team_admin': team_admin, 'org_admin': org_admin,
                                                    'week_time_spent_nonedit': week_time_spent_nonedit,
                                                    'edit_flag': edit_flag, 'next_week': next_week,
                                                    'previous_week': previous_week, 's_date': s_date, 'e_date': e_date,
                                                    'requested_user': requested_user.id,
                                                    'requested_flag': requested_user_flag,
                                                    'timesheet_flag': timesheet_flag, 'member_flag': member_flag})


class TimeSheetSubmissionRequest(TemplateView):

    template_name = 'submission_request.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TimeSheetSubmissionRequest, self).dispatch(request, *args, **kwargs)

    #def get_template_names(self):
    #    return ['submission_request.html']

    def get(self, request, *args, **kwargs):
        sent_to = request.GET['sent_to']

        if int(sent_to) != self.request.user.id:
            raise Http404("Page not found")

        context = self.get_context_data()

        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        pk = self.request.GET['sent_from']
        user = User.objects.get(id= int(pk))
        context = super(TimeSheetSubmissionRequest, self).get_context_data(**kwargs)
        start_date = self.request.GET['date']
        start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        start_date = start_date - timedelta(days=start_date.weekday())
        end_date = start_date+timedelta(days=6)
        context['team_admin'] = ""
        context['org_admin'] = ""
        context['timesheet_flag'] = ""

        if TimeSheetData.objects.filter(user=self.request.user):
            context['timesheet_flag'] = True

        context['pk'] = pk
        context['start_date'] = start_date.strftime('%m/%d/%Y')
        timesheets = TimeSheetData.objects.filter(user=user,
                                                  timesheetweekdata__date__range=[start_date,end_date]).distinct()
        week_time_spent_nonedit = []

        for timesheet in timesheets:
            count = 1
            initial_timesheet_data = {'status': '', 'project': '', 'issue_id': '', 'issue_description': '', 'mon': '',
                                      'tue': '', 'wed': '', 'thu': '', 'fri': '', 'sat': '', 'sun': ''}
            weekdata = TimeSheetWeekData.objects.filter(timesheet=timesheet).order_by('date')
            initial_timesheet_data['status'] = timesheet.status
            obj = Project.objects.get(id=timesheet.project_id)
            initial_timesheet_data['project'] = obj.project_name
            initial_timesheet_data['issue_id'] = timesheet.issue_id
            initial_timesheet_data['issue_description'] = timesheet.issue_description

            for data in weekdata:
                if count == 1:
                    initial_timesheet_data['mon'] = data.time_spent
                elif count == 2:
                    initial_timesheet_data['tue'] = data.time_spent
                elif count == 3:
                    initial_timesheet_data['wed'] = data.time_spent
                elif count == 4:
                    initial_timesheet_data['thu'] = data.time_spent
                elif count == 5:
                    initial_timesheet_data['fri'] = data.time_spent
                elif count == 6:
                    initial_timesheet_data['sat'] = data.time_spent
                elif count == 7:
                    initial_timesheet_data['sun'] = data.time_spent
                count += 1

            week_time_spent_nonedit.append(initial_timesheet_data)

        context['weekly_timesheet'] = week_time_spent_nonedit

        if ProjectAssignment.objects.filter(assigned_to=self.request.user.id, admin_flag=True):
            context['team_admin'] = "True"

        if self.request.user.user_type == 1:
            context['org_admin'] = "True"

        return context

class TimeSheetStatus(TemplateView):

    template_name = 'timesheet_status.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TimeSheetStatus, self).dispatch(request,*args, **kwargs)

    #def get_template_names(self):
    #    return ['timesheet_status.html']

    def get_context_data(self, **kwargs):
        context = super(TimeSheetStatus, self).get_context_data(**kwargs)
        cursor = connection.cursor()
        cursor.execute("SELECT date_trunc('week',tw.date),td.status FROM timetracking_timesheetdata td INNER JOIN timetracking_timesheetweekdata tw ON tw.timesheet_id = td.id  where td.user_id = %s  GROUP BY date_trunc('week',tw.date),td.status order by td.status",[self.request.user.id])
        results = cursor.fetchall()
        timesheet_status = []
        dummy_date = []
        copy_date = []
        for result in results:
            date = result[0]
            date = date.strftime('%m/%d/%Y')

            if date not in dummy_date:
                dummy_date.append(date)
            else:
                copy_date.append(date)

        for result in results:
            time_list = {'status': '', 'start_date': '', 'end_date': ''}
            start_date = result[0]
            end_date = start_date+timedelta(days=6)
            start_date = start_date.strftime('%m/%d/%Y')
            end_date = end_date.strftime('%m/%d/%Y')

            if start_date in copy_date:
                time_list['status'] = 'Pending'

            else:
                if result[1] == 0:
                    time_list['status'] = 'Pending'
                else:
                    time_list['status'] = 'Submitted'

            time_list['start_date'] = start_date
            time_list['end_date'] = end_date

            if not any(d['start_date'] == start_date for d in timesheet_status):
                timesheet_status.append(time_list)

        context['timesheet_status'] = timesheet_status
        context['team_admin'] = ""
        context['org_admin'] = ""
        context['timesheet_flag'] = ""

        if TimeSheetData.objects.filter(user=self.request.user):
            context['timesheet_flag'] = True

        if ProjectAssignment.objects.filter(assigned_to=self.request.user.id, admin_flag=True):
            context['team_admin'] = "True"

        if self.request.user.user_type == 1:
            context['org_admin'] = "True"

        return context


class GraphicalAnalysis(TemplateView):
    template_name = 'graphical_analysis.html'

    def get_context_data(self, **kwargs):
        context = super(GraphicalAnalysis, self).get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user.username)
        project = Project.objects.filter(projectassignment__assigned_to=user, projectassignment__admin_flag=True)
        context['team_admin'] = ""
        context['org_admin'] = ""

        if ProjectAssignment.objects.filter(assigned_to=self.request.user.id, admin_flag=True):
            context['team_admin'] = "True"
            context['members'] = User.objects.filter(projectassignment__project=project,
                                                     projectassignment__admin_flag=False).distinct()
            context['projects'] = project

        if self.request.user.user_type == 1:
            context['org_admin'] = "True"
            context['members'] = User.objects.filter(~Q(id=self.request.user.id))
            context['projects'] = Project.objects.all()

        return context



class GraphView(View):
    template_name = 'highchart.html'

    def post(self, request, *args, **kwargs):
        date = self.request.POST.get('date')
        graph_type = self.request.POST['graph_type']
        if self.request.POST.get('filter') == 'member':
            item_list = self.request.POST.getlist('member')
            flag = 0

        else:
            item_list = self.request.POST.getlist('project')
            flag = 1
        graph_data = {'date' : '', 'item_list': '', 'graph_type': '', 'flag': ''}
        graph_data['date'] = date
        graph_data['item_list'] = item_list
        graph_data['graph_type'] = graph_type
        graph_data['flag'] = flag

        return render(request, self.template_name, {'date': date, 'item_list': json.dumps(item_list),
                                                    'graph_type': graph_type, 'flag': flag,
                                                    'graph_data': json.dumps(graph_data) })




class BarView(HighChartsBarView):
    #categories = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    y_axis_title = 'Time Spent'
    title = 'Graphical Analysis'

    @property
    def series(self):
        categories = self.categories
        result = []
        start_date = self.request.GET['date']
        start_date = datetime.strptime(start_date, '%m/%d/%Y')
        start_date = start_date - timedelta(days = start_date.weekday())
        formatted_date = start_date

        for i in range(1, 8, 1):
            categories.append(formatted_date.strftime('%m/%d/%Y'))
            formatted_date = formatted_date+timedelta(days=1)

        end_date = start_date+timedelta(days=6)
        user = User.objects.get(id=self.request.user.id)
        item_list = self.request.GET.getlist('item_list[]')

        #graph filtered on the basis of members
        if self.request.GET['flag'] == '0':
            if self.request.GET['graph_type'] == 'split':
                for name in item_list:
                    data = []
                    current_user = User.objects.get(username=name)
                    cursor = connection.cursor()
                    cursor.execute("select sum(time_spent), date from timetracking_timesheetweekdata where date >= %s and date <= %s and timesheet_id in (select td.id from timetracking_timesheetdata td inner join timetracking_timesheetweekdata tw on td.id = tw.timesheet_id and td.user_id = %s and tw.date >= %s and tw.date <= %s ) group by date order by date",[start_date,end_date,current_user.id,start_date,end_date])
                    results = cursor.fetchall()

                    for res in results:
                        data.append(int(res[0]))

                    result.append({'name': name, "data": data})

                return result

            else:
                data = []
                cursor = connection.cursor()
                cursor.execute("select sum(time_spent),date from timetracking_timesheetweekdata where date >= %s and date <= %s and timesheet_id in (select td.id from timetracking_timesheetdata td inner join timetracking_timesheetweekdata tw on td.id = tw.timesheet_id and td.user_id in (select id from userinfo_customuser where username in %s) and tw.date >= %s and tw.date <= %s) group by date order by date",[start_date,end_date,tuple(item_list),start_date,end_date])
                results = cursor.fetchall()

                for res in results:
                    data.append(int(res[0]))

                result.append({"name": "Aggregate", "data": data})

                return result

        else:
            if self.request.GET['graph_type'] == 'split':

                for project in item_list:
                    data = []
                    current_project = Project.objects.get(project_name=project)
                    cursor = connection.cursor()
                    cursor.execute("select sum(time_spent), date from timetracking_timesheetweekdata where date >= %s and date <= %s and timesheet_id in (select td.id from timetracking_timesheetdata td inner join timetracking_timesheetweekdata tw on td.id = tw.timesheet_id and td.project_id = %s and tw.date >= %s and tw.date <= %s ) group by date order by date",[start_date,end_date,current_project.id,start_date,end_date])
                    results = cursor.fetchall()

                    for res in results:
                        data.append(int(res[0]))

                    result.append({'name': project, "data": data})

                return result

            else:
                data = []
                cursor = connection.cursor()
                cursor.execute("select sum(time_spent),date from timetracking_timesheetweekdata where date >= %s and date <= %s and timesheet_id in (select td.id from timetracking_timesheetdata td inner join timetracking_timesheetweekdata tw on td.id = tw.timesheet_id and td.project_id in (select id from projects_project where project_name in %s) and tw.date >= %s and tw.date <= %s) group by date order by date",[start_date,end_date,tuple(item_list),start_date,end_date])
                results = cursor.fetchall()

                for res in results:
                    data.append(int(res[0]))

                result.append({"name": "Aggregate", "data": data})

                return result


class DataView(View):

    csv_filename = 'csvfile.csv'

    def post(self, request, *args, **kwargs):
        graph_data = self.request.POST['graph_data']
        graph_data = json.loads(graph_data)
        start_date = datetime.strptime(graph_data['date'], '%m/%d/%Y')
        start_date = start_date - timedelta(days=start_date.weekday())
        end_date = start_date+timedelta(days=6)
        dummy_start_date = start_date
        row_date = dummy_start_date
        item_list = graph_data['item_list']
        if graph_data['flag'] == 0:
            id_list = User.objects.filter(username__in=item_list).values_list('id', flat=True)

        else:
            id_list = Project.objects.filter(project_name__in=item_list).values_list('id',flat=True)
        new_list = []
        for ids in id_list:
            new_list.append(ids)

        id_key_list = {_id: index for index, _id in enumerate(new_list)}

        len_list = len(id_list)
        response = HttpResponse(content_type='text/csv')
        cd = 'attachment; filename="{0}"'.format(self.csv_filename)
        response['Content-Disposition'] = cd
        writer = csv.writer(response)
        #graph filtered on the basis of members
        if graph_data['flag'] == 0:
            if graph_data['graph_type'] == 'split':

                test_query = TimeSheetData.objects.filter(timesheetweekdata__date__range=[start_date,end_date],user_id__in = id_list).values('user_id','timesheetweekdata__date').annotate(total_time=Sum('timesheetweekdata__time_spent')).order_by('timesheetweekdata__date')
                query_length = len(test_query)
                initial_length = len_list+1
                result = []
                for i in range(0, 7, 1):
                    data = [0]*initial_length
                    result.append(data)
                #result = [[0] * initial_length ] * 7
                for i in range(0, 7, 1):
                    result[i][0] = row_date.strftime('%m/%d/%Y')
                    row_date += timedelta(days=1)
                row_date = dummy_start_date
                counter = 0
                data_length = 0
                test_data = [0] * initial_length
                flag = 0
                for test in test_query:
                    counter += 1
                    if test['timesheetweekdata__date'].strftime('%m/%d/%Y') == row_date.strftime('%m/%d/%Y'):
                        if flag == 0:
                            test_data[0] = row_date.strftime('%m/%d/%Y')
                            flag = 1

                        test_data[id_key_list[test['user_id']]+1] = test['total_time']

                        #if test['user_id'] in new_list:
                        #    test_data[new_list.index(test['user_id'])+1] = test['total_time']
                        if counter == query_length:
                            result[data_length] = test_data

                    else:
                        result[data_length] = test_data
                        data_length += 1
                        row_date += timedelta(days=1)
                        test_data = [0] * initial_length
                        test_data[0] = row_date.strftime('%m/%d/%Y')
                        test_data[id_key_list[test['user_id']]+1] = test['total_time']
                        #if test['user_id'] in new_list:
                        #    test_data[new_list.index(test['user_id'])+1] = test['total_time']

            else:

                test_query = TimeSheetData.objects.filter(timesheetweekdata__date__range=[start_date,end_date],user_id__in = id_list).values('timesheetweekdata__date').annotate(total_time=Sum('timesheetweekdata__time_spent')).order_by('timesheetweekdata__date')
                result = []
                for i in range(0, 7, 1):
                    data = [0]*2
                    result.append(data)
                #result = [[0] * initial_length ] * 7
                for i in range(0, 7, 1):
                    result[i][0] = row_date.strftime('%m/%d/%Y')
                    row_date += timedelta(days=1)
                row_date = dummy_start_date
                for test in test_query:
                    data = []
                    data.append(row_date.strftime('%m/%d/%Y'))
                    data.append(test['total_time'])
                    row_date += timedelta(days=1)
                    result.append(data)


        else:

            if graph_data['graph_type'] == 'split':
                test_query = TimeSheetData.objects.filter(timesheetweekdata__date__range=[start_date,end_date],project_id__in = id_list).values('project_id','timesheetweekdata__date').annotate(total_time=Sum('timesheetweekdata__time_spent')).order_by('timesheetweekdata__date')
                query_length = len(test_query)
                initial_length = len_list+1
                result = []
                for i in range(0, 7, 1):
                    data = [0]*initial_length
                    result.append(data)
                #result = [[0] * initial_length ] * 7
                for i in range(0, 7, 1):
                    result[i][0] = row_date.strftime('%m/%d/%Y')
                    row_date += timedelta(days=1)
                row_date = dummy_start_date
                counter = 0
                data_length = 0
                test_data = [0] * initial_length
                flag = 0
                for test in test_query:
                    counter += 1
                    if test['timesheetweekdata__date'].strftime('%m/%d/%Y') == row_date.strftime('%m/%d/%Y'):
                        if flag == 0:
                            test_data[0] = row_date.strftime('%m/%d/%Y')
                            flag = 1
                        test_data[id_key_list[test['project_id']]+1] = test['total_time']
                        #if test['project_id'] in new_list:
                        #    test_data[new_list.index(test['project_id'])+1] = test['total_time']
                        if counter == query_length:
                            result[data_length] = test_data

                    else:
                        result[data_length] = test_data
                        data_length += 1
                        row_date += timedelta(days=1)
                        test_data = [0] * initial_length
                        test_data[0] = row_date.strftime('%m/%d/%Y')
                        test_data[id_key_list[test['project_id']]+1] = test['total_time']
                        #if test['project_id'] in new_list:
                        #    test_data[new_list.index(test['project_id'])+1] = test['total_time']
            else:
                test_query = TimeSheetData.objects.filter(timesheetweekdata__date__range=[start_date,end_date],project_id__in = id_list).values('timesheetweekdata__date').annotate(total_time=Sum('timesheetweekdata__time_spent')).order_by('timesheetweekdata__date')
                result = []
                for i in range(0, 7, 1):
                    data = [0]*2
                    result.append(data)
                #result = [[0] * initial_length ] * 7
                for i in range(0, 7, 1):
                    result[i][0] = row_date.strftime('%m/%d/%Y')
                    row_date += timedelta(days=1)
                row_date = dummy_start_date
                for test in test_query:
                    data = []
                    data.append(row_date.strftime('%m/%d/%Y'))
                    data.append(test['total_time'])
                    row_date += timedelta(days=1)
                    result.append(data)


        fieldnames = ['Date']
        if graph_data['graph_type'] == 'split':
            for item in item_list:
                fieldnames.append(item)
        else:
            fieldnames.append('Aggregate')

        writer.writerow(fieldnames)
        print result
        for row in result:
            writer.writerow(row)

        return response