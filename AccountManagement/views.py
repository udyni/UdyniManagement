from django.shortcuts import render
from django.contrib.auth import views as auth_views

# Create your views here.
class LoginView(auth_views.LoginView):
    template_name = 'AccountManagement/login.html'

class LogoutView(auth_views.LogoutView):
    template_name = 'AccountManagement/logged_out.html'

