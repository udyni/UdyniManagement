from django.urls import reverse_lazy
from django.shortcuts import render
from .forms import RegistrationForm, SetPasswordForm, PasswordChangeForm
from django.views.generic.edit import View, FormView
from django.contrib.auth import views as auth_views
from django.views.generic.list import ListView


# Create your views here.
class LoginView(auth_views.LoginView):
    template_name = 'AccountManagement/login.html'


class LogoutView(auth_views.LogoutView):
    template_name = 'AccountManagement/logged_out.html'


class RegistrationFormView(FormView):
    template_name = 'AccountMangement/registration.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('registration_complete')


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "AccountManagement/passwordreset.html"


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "AccountManagement/passwordreset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "AccountManagement/passwordreset_confirm.html"
    form_class = SetPasswordForm


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "AccountManagement/passwordreset_complete.html"


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "AccountManagement/passwordchange.html"
    form_class = PasswordChangeForm


class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = "AccountManagement/passwordchange_done.html"


class AccountRegistration(View):
    pass


class AccountProfileView(View):
    pass


class PermissionListView(ListView):
    pass