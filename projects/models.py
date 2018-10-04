from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Project(models.Model):
    ACTIVE = 0
    COMPLETE = 1
    PROJECT_STATUS = (
        (ACTIVE, 'Active'),
        (COMPLETE,'Complete'),
    )
    project_id = models.IntegerField()
    project_name = models.CharField(max_length=30)
    description = models.TextField()
    status = models.IntegerField(default=ACTIVE, choices=PROJECT_STATUS)

    def __unicode__(self):
        return self.project_name

class ProjectAssignment(models.Model):

    project = models.ForeignKey(Project)
    assigned_to = models.ForeignKey(User)
    admin_flag = models.BooleanField(default=False)



class ActivityLog(models.Model):
    ADD = 0
    MODIFY = 1
    DELETE = 2

    ACTIVITY_TYPE = (
        (ADD, 'Add'),
        (MODIFY,'Modify'),
        (DELETE, 'Delete'),
    )
    user = models.ForeignKey(User)
    project = models.ForeignKey(Project)
    date = models.DateTimeField()
    activity_type = models.IntegerField(choices=ACTIVITY_TYPE)







# Create your models here.
