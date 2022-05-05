from django.urls import path, reverse_lazy
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path('gae/', views.GAElist.as_view(), name='acc_gae_list'),
    path('gae/add', views.GAEadd.as_view(), name='acc_gae_add'),
    path('gae/<int:pk>/mod', views.GAEmod.as_view(), name='acc_gae_mod'),
    path('gae/<int:pk>/del', views.GAEdel.as_view(), name='acc_gae_del'),
    path('residui/', views.GAEResidui.as_view(), name='acc_gae_residui'),
    path('situazione/', views.GAESituazione.as_view(), name='acc_gae_situazione'),
    path('impegni/', views.GAEImpegni.as_view(), name='acc_gae_impegni'),
    path('ajax/<int:gae>/situazione', views.GAEAjaxSituazione.as_view(), name='acc_ajax_gae_situazione'),
    path('ajax/<int:gae>/impegni', views.GAEAjaxImpegni.as_view(), name='acc_ajax_gae_impegni'),
    #path('ajax/<int:gae>/impegni/detail', views.GAEAjaxImpegni.as_view(), name='acc_ajax_gae_impegni_mandati'),
]

menu = {
    'name': 'Accounting',
    'link': '',
    'icon': 'fa-sack-dollar',
    'subsections': [
        {
            'name': 'GAE',
            'link': reverse_lazy('acc_gae_list'),
            'permissions': [],
        },
        {
            'name': "Up to date 'residui'",
            'link': reverse_lazy('acc_gae_residui'),
            'permissions': [],
        },
        {
            'name': "'Situazione' GAE",
            'link': reverse_lazy('acc_gae_situazione'),
            'permissions': [],
        },
        {
            'name': "'Impegni' GAE",
            'link': reverse_lazy('acc_gae_impegni'),
            'permissions': [],
        },
        {
            'name': 'SIGLA manual',
            'link': reverse_lazy('sigla_manual_main'),
            'permissions': [],
        }
    ],
    'permissions': [],
}