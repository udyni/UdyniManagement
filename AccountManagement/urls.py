from django.urls import path, reverse_lazy
from django.views.generic.base import RedirectView

from . import views


urlpatterns = [
    path('login/', views.LoginView.as_view(), name="account_login"),
    path('logout/', views.LogoutView.as_view(), name="account_logout"),
]