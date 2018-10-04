from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    MEMBER= 0
    ORG_ADMIN = 1

    USER_TYPE = (
        (MEMBER, 'Member'),
        (ORG_ADMIN, 'Org-Admin'),
    )
    user_type = models.IntegerField(default=0, choices= USER_TYPE)


# Create your models here.
