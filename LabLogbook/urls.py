from django.urls import path, reverse_lazy
from UdyniManagement.views import EmptyView

from . import views

urlpatterns = [
    path('', EmptyView.as_view(), name='lablogbook_index'),

    path('laboratories/', views.LaboratoryList.as_view(), name='laboratory_view'),
    path('laboratories/add', views.LaboratoryCreate.as_view(), name='laboratory_add'),
    path('laboratories/<int:pk>/modify', views.LaboratoryUpdate.as_view(), name='laboratory_mod'),
    path('laboratories/<int:pk>/delete', views.LaboratoryDelete.as_view(), name='laboratory_del'),
]

menu = {
    'name': "Lab Logbook",
    'link': reverse_lazy('lablogbook_index'),
    'icon': 'fa-solid fa-book',
    'subsections': [
        {
            'name': 'Laboratories',
            'link': reverse_lazy('laboratory_view'),
            'permissions': ['Laboratory.laboratory_view'],
        },
        # TODO
        # {
        #     'name': 'Experimental Stations',
        #     'link': reverse_lazy('experimentalstation_view'),
        #     'permissions': [],
        # },
        # {
        #     'name': 'Samples',
        #     'link': reverse_lazy('sample_view'),
        #     'permissions': [],
        # },
    ],
    'permissions': [],
}