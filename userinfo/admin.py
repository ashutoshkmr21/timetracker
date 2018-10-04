from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from userinfo.models import CustomUser
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
admin.site.unregister(Site)
admin.site.unregister(Group)
from django.contrib.auth import get_user_model
User = get_user_model()


class MyUserCreationForm(UserCreationForm):

    class Meta:
        model = User
    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])



class CustomUserAdmin(UserAdmin):
    list_display = ['id','username','email','user_type']
    ordering = ['id']
    add_form = MyUserCreationForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2','user_type')}
        ),
    )




admin.site.register(CustomUser,CustomUserAdmin)

# Register your models here.
