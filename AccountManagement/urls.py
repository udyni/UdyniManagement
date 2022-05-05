from django.urls import path, reverse_lazy
from django.views.generic.base import RedirectView

from . import views


urlpatterns = [
    path('login/', views.LoginView.as_view(), name="account_login"),
    path('logout/', views.LogoutView.as_view(), name="account_logout"),
    path('register/', views.AccountRegistration.as_view(), name="account_register"),
    path('profile/', views.AccountProfileView.as_view(), name="account_profile"),
    path('reset/', views.PasswordResetView.as_view(), name="account_password_reset"),
    path('permissions/', views.PermissionListView.as_view(), name="account_permissions")
]