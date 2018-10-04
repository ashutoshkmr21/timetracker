import datetime
from django.dispatch import Signal
from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete
from django.db import models
from projects.models import Project
from django.contrib.auth import get_user_model
from projects.models import ActivityLog
from timetracking.signals import *
User = get_user_model()


class TimeSheetData(models.Model):
    EDITABLE = 0
    PARTIALLY_FROZEN = 1
    FROZEN = 2

    TIMESHEET_STATUS = (
        (EDITABLE, 'Editable'),
        (PARTIALLY_FROZEN,'Partially-Frozen'),
        (FROZEN, 'Frozen'),
    )

    user = models.ForeignKey(User)
    project = models.ForeignKey(Project)
    issue_id = models.IntegerField()
    issue_description = models.CharField(max_length=60)
    status = models.IntegerField(default=EDITABLE, choices=TIMESHEET_STATUS)
    def __unicode__(self):
        return "{}:{}:{}".format(self.user, self.project, self.issue_id)



class TimeSheetWeekData(models.Model):
    timesheet = models.ForeignKey(TimeSheetData)
    time_spent = models.IntegerField(default=0)
    date = models.DateTimeField()

@receiver(post_save, sender=TimeSheetData)
def timesheet_added(sender,**kwargs):
    obj= kwargs['instance']
    ActivityLog.objects.create(user = obj.user,project = obj.project, date = datetime.datetime.now(),activity_type = 0)

@receiver(post_delete, sender=TimeSheetData)
def timesheet_delete(sender,**kwargs):
    obj = kwargs['instance']
    ActivityLog.objects.create(user = obj.user,project = obj.project, date = datetime.datetime.now(),activity_type = 2)

def timesheet_updated(**kwargs):
    ActivityLog.objects.create(user = kwargs['user'],project = kwargs['project'], date = datetime.datetime.now(),activity_type = 1)

timesheet_signal.connect(timesheet_updated)

# Create your models here.
