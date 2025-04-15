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
    path('laboratories/add', views.LaboratoryCreate.as_view(), name='laboratory_add'),
    path('laboratories/<int:pk>/modify', views.LaboratoryUpdate.as_view(), name='laboratory_mod'),
    path('laboratories/<int:pk>/delete', views.LaboratoryDelete.as_view(), name='laboratory_del'),
    path('laboratories/<int:laboratory_id>/experimentalstations/add', views.ExperimentalStationCreate.as_view(), name='experimentalstation_add'),
    path('experimentalstations/<int:pk>/modify', views.ExperimentalStationUpdate.as_view(), name='experimentalstation_mod'),
    path('experimentalstations/<int:pk>/delete', views.ExperimentalStationDelete.as_view(), name='experimentalstation_del'),

    # Experiments for experimental station
    path('experimentalstations/<int:station_id>/experiments/', views.ExperimentList.as_view(), name='experiment_view'),
    path('experimentalstations/<int:station_id>/experiments/add', views.ExperimentCreate.as_view(), name='experiment_add'),
    path('experimentalstations/<int:station_id>/experiments/<int:pk>/modify', views.ExperimentUpdate.as_view(), name='experiment_mod'),
    path('experimentalstations/<int:station_id>/experiments/<int:pk>/delete', views.ExperimentDelete.as_view(), name='experiment_del'),
    path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/add_sample', views.SampleForExperimentAdd.as_view(), name='experiment_sample_add'),
    # note that here pk is the key of the SampleForExperiment object, not of the sample object
    path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/remove_sample/<int:pk>', views.SampleForExperimentRemove.as_view(), name='experiment_sample_del'),

    # look at personnel reporting page for arrrow that goes down
    # path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/measurements/', views.MeasurementList.as_view(), name='experiment_measurement_view'),
    # path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/measurements/add', views.MeasurementAdd.as_view(), name='experiment_measurement_add'),
    # path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/measurements/<int:pk>/modify', views.MeasurementUpdate.as_view(), name='experiment_measurement_mod'),
    # path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/measurements/<int:pk>/delete', views.MeasurementDelete.as_view(), name='experiment_measurement_del'),
    
    
    # path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/measurements/<int:measurement_id>/add', views.FileAdd.as_view(), name='measurement_file_add'),
    # path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/measurements/<int:measurement_id>/add', views.FileUpdate.as_view(), name='measurement_file_mod'),
    # path('experimentalstations/<int:station_id>/experiments/<int:experiment_id>/measurements/<int:measurement_id>/add', views.FileDelete.as_view(), name='measurement_file_del'),



    # Logbook for experiment TODO
    # path('labs_and_experimentalstations/experimentalstations/<int:station_id>/experiments/<int:experiment_id>/logbook', views.CommentList.as_view(), name='comment_view'),
    # path('labs_and_experimentalstations/experimentalstations/<int:station_id>/experiments/<int:experiment_id>/logbook/add', views.CommentCreate.as_view(), name='comment_add'),
    # path('labs_and_experimentalstations/experimentalstations/<int:station_id>/experiments/<int:experiment_id>/logbook/<int:pk>/modify', views.CommentContentCreate.as_view(), name='commentcontent_add'),
    # path('labs_and_experimentalstations/experimentalstations/<int:station_id>/experiments/<int:experiment_id>/logbook/<int:pk>/reply', views.CommentReply.as_view(), name='comment_reply'),
    # path('labs_and_experimentalstations/experimentalstations/<int:station_id>/experiments/<int:experiment_id>/logbook/<int:pk>/delete', views.CommentList.as_view(), name='comment_del'),

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