from . import views
from UdyniManagement.views import EmptyView

from django.urls import path, reverse_lazy



urlpatterns = [
    path('', EmptyView.as_view(), name='lablogbook_index'),
    
    # Samples
    path('samples/', views.SampleList.as_view(), name='sample_view'),
    path('samples/add', views.SampleCreate.as_view(), name='sample_add'),
    path('samples/<int:sample_id>/modify', views.SampleUpdate.as_view(), name='sample_mod'),
    path('samples/<int:sample_id>/delete', views.SampleDelete.as_view(), name='sample_del'),

    # Experimental Stations
    path('experimentalstations/', views.ExperimentalStationList.as_view(), name='experimentalstation_view'),
    path('experimentalstations/laboratories/add', views.LaboratoryCreate.as_view(), name='laboratory_add'),
    path('experimentalstations/laboratories/<int:laboratory_id>/modify', views.LaboratoryUpdate.as_view(), name='laboratory_mod'),
    path('experimentalstations/laboratories/<int:laboratory_id>/delete', views.LaboratoryUpdate.as_view(), name='laboratory_del'),    
    path('experimentalstations/laboratories/<int:laboratory_id>/add', views.ExperimentalStationCreate.as_view(), name='experimentalstation_add'),
    path('experimentalstations/<int:station_id>/modify', views.ExperimentalStationUpdate.as_view(), name='experimentalstation_mod'),
    path('experimentalstations/<int:station_id>/delete', views.ExperimentalStationDelete.as_view(), name='experimentalstation_del'),

    # Experiments for experimental station
    # TODO
    # look at personnel reporting page for arrrow that goes down
    # give the possibility of adding a sample to an experiment
    path('experimentalstations/<int:station_id>/experiments/', views.ExperimentList.as_view(), name='experiment_view'),
    path('experimentalstations/<int:station_id>/experiments/add', views.ExperimentCreate.as_view(), name='experiment_add'),
    path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/modify', views.ExperimentUpdate.as_view(), name='experiment_mod'),
    path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/delete', views.ExperimentDelete.as_view(), name='experiment_del'),
    path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/add_sample/', views.ExperimentSampleAdd.as_view(), name='experiment_sample_add'),
    path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/remove_sample/<int:sample_id>', views.ExperimentSampleRemove.as_view(), name='experiment_sample_del'),

    # Logbook for experiment TODO
    # path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/logbook', views.LogbookList.as_view(), name='logbook_view'),
]

menu = {
    'name': "Lab Logbook",
    'link': reverse_lazy('lablogbook_index'),
    'icon': 'fa-solid fa-book',
    'subsections': [
        {
            'name': 'Experimental Stations',
            'link': reverse_lazy('experimentalstation_view'),
            'permissions': ['Laboratory.laboratory_view', 'ExperimentalStation.experimentalstation_view'],
        },
        {
            'name': 'Samples',
            'link': reverse_lazy('sample_view'),
            'permissions': ['Sample.sample_view',],
        },
    ],
    'permissions': [],
}