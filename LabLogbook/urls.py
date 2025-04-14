from . import views
from UdyniManagement.views import EmptyView

from django.urls import path, reverse_lazy



urlpatterns = [
    path('', EmptyView.as_view(), name='lablogbook_index'),
    
    # Samples
    path('samples/', views.SampleList.as_view(), name='sample_view'),
    path('samples/add', views.SampleCreate.as_view(), name='sample_add'),
    path('samples/<int:pk>/modify', views.SampleUpdate.as_view(), name='sample_mod'),
    path('samples/<int:pk>/delete', views.SampleDelete.as_view(), name='sample_del'),

    # Experimental Stations
    path('labs_and_experimentalstations/', views.LabAndExperimentalStationList.as_view(), name='lab_and_experimentalstation_view'),
    path('labs_and_experimentalstations/laboratories/add', views.LaboratoryCreate.as_view(), name='laboratory_add'),
    path('labs_and_experimentalstations/laboratories/<int:pk>/modify', views.LaboratoryUpdate.as_view(), name='laboratory_mod'),
    path('labs_and_experimentalstations/laboratories/<int:pk>/delete', views.LaboratoryDelete.as_view(), name='laboratory_del'),
    path('labs_and_experimentalstations/laboratories/<int:laboratory_id>/experimentalstations/add', views.ExperimentalStationCreate.as_view(), name='experimentalstation_add'),
    path('labs_and_experimentalstations/experimentalstations/<int:pk>/modify', views.ExperimentalStationUpdate.as_view(), name='experimentalstation_mod'),
    path('labs_and_experimentalstations/experimentalstations/<int:pk>/delete', views.ExperimentalStationDelete.as_view(), name='experimentalstation_del'),

    # Experiments for experimental station
    # TODO
    # look at personnel reporting page for arrrow that goes down
    # give the possibility of adding a sample to an experiment
    path('labs_and_experimentalstations/experimentalstations/<int:station_id>/experiments/', views.ExperimentList.as_view(), name='experiment_view'),
    path('labs_and_experimentalstations/experimentalstations/<int:station_idk>/experiments/add', views.ExperimentCreate.as_view(), name='experiment_add'),
    path('labs_and_experimentalstations/experimentalstations/<int:station_id>/experiments/<int:pk>/modify', views.ExperimentUpdate.as_view(), name='experiment_mod'),
    path('labs_and_experimentalstations/experimentalstations/<int:station_id>/experiments/<int:pk>/delete', views.ExperimentDelete.as_view(), name='experiment_del'),
    path('labs_and_experimentalstations/experimentalstations/<int:station_id>/experiments/<int:experiment_id>/add_sample/', views.ExperimentSampleAdd.as_view(), name='experiment_sample_add'),
    path('labs_and_experimentalstations/experimentalstations/<int:station_id>/experiments/<int:experiment_id>/remove_sample/<int:pk>', views.ExperimentSampleRemove.as_view(), name='experiment_sample_del'),

    # Logbook for experiment TODO
    # path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/logbook', views.LogbookList.as_view(), name='logbook_view'),
]

menu = {
    'name': "Lab Logbook",
    'link': reverse_lazy('lablogbook_index'),
    'icon': 'fa-solid fa-book',
    'subsections': [
        {
            'name': 'Labs & Exp Stations',
            'link': reverse_lazy('lab_and_experimentalstation_view'),
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