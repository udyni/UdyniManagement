"""UdyniManagement URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from . import views
from .menu import menu_include


urlpatterns = [
    path('', views.EmptyView.as_view(), name="main_page"),
    path('accounts/', include('AccountManagement.urls')),
    path('projects/', include('Projects.urls')),
    path('accounting/', include('Accounting.urls')),
    path('reporting/', include('FinancialReporting.urls')),
    path('sigla/', include('sigla.urls')),
    path('admin/', admin.site.urls),
]

menu = [
    {
        'name': 'Project Management',
        'sections': [
            menu_include('Projects.urls'),
            menu_include('Accounting.urls'),
            menu_include('FinancialReporting.urls'),
        ],
    },
    {
        'name': 'Services',
        'sections': [
            {
                'name': 'Request VPN certificate',
                'link': '/git',
                'subsections': [],
                'permissions': [],
            },
            {
                'name': 'Git',
                'link': '/git',
                'subsections': [],
                'permissions': [],
            },
            {
                'name': 'Wiki',
                'link': '/xwiki',
                'subsections': [],
                'permissions': [],
            },
            {
                'name': 'Postgres Admin',
                'link': '/pgadmin',
                'subsections': [],
                'permissions': ['is_staff', ],
            },
        ],
    },
]
