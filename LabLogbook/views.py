from .models import Laboratory, Sample, ExperimentalStation, Experiment, SampleForExperiment, Measurement, File, Comment, CommentContent
from .forms import CommentForm, CommentContentForm
from UdyniManagement.views import ListViewMenu, CreateViewMenu, UpdateViewMenu, DeleteViewMenu
from UdyniManagement.menu import UdyniMenu

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views import View
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy


# =============================================
# SAMPLE
#
class SampleList(PermissionRequiredMixin, ListViewMenu):
    model = Sample
    permission_required = 'Sample.sample_view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Samples"
        context['can_edit'] = self.request.user.has_perm('Sample.sample_manage')
        return context

class SampleCreate(PermissionRequiredMixin, CreateViewMenu):
    model = Sample
    fields = ['name', 'material', 'substrate', 'manufacturer', 'description', 'reference', 'author']
    permission_required = 'Sample.sample_manage'
    template_name = "UdyniManagement/generic_form.html"
    
    def get_success_url(self):
        return reverse_lazy('sample_view')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add new sample"
        context['back_url'] = self.get_success_url()
        return context

class SampleUpdate(PermissionRequiredMixin, UpdateViewMenu):
    model = Sample
    fields = ['name', 'material', 'substrate', 'manufacturer', 'description', 'reference', 'author']
    permission_required = 'Sample.sample_manage'
    template_name = "UdyniManagement/generic_form.html"

    def get_success_url(self):
        return reverse_lazy('sample_view')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Modify sample"
        context['back_url'] = self.get_success_url()
        return context

class SampleDelete(PermissionRequiredMixin, DeleteViewMenu):
    model = Sample
    permission_required = 'Sample.sample_manage'
    template_name = "UdyniManagement/confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy('sample_view')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete sample"
        context['message'] = f"Are you sure you want to delete the sample: {context['sample']}?"
        context['back_url'] = self.get_success_url()
        return context
    

# =============================================
# LABORATORY & EXPERIMENTAL STATION
#
class LabAndExperimentalStationList(PermissionRequiredMixin, ListViewMenu): # This view is used for the 'Labs & Experimental Stations' page
    model = ExperimentalStation
    permission_required = 'Laboratory.laboratory_view', 'ExperimentalStation.experimentalstation_view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Labs & Experimental Stations"
        context['can_edit_lab'] = self.request.user.has_perm('Laboratory.laboratory_manage')
        context['can_edit_station'] = self.request.user.has_perm('ExperimentalStation.experimentalstation_manage')
        context['laboratory_list'] = Laboratory.objects.all()
        return context


# =============================================
# LABORATORY
#
class LaboratoryCreate(PermissionRequiredMixin, CreateViewMenu):
    model = Laboratory
    fields = ['name', 'description', 'location']
    permission_required = 'Laboratory.laboratory_manage'
    template_name = "UdyniManagement/generic_form.html"
    
    def get_success_url(self):
        return reverse_lazy('lab_and_experimentalstation_view')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add new laboratory"
        context['back_url'] = self.get_success_url()
        return context

class LaboratoryUpdate(PermissionRequiredMixin, UpdateViewMenu):
    model = Laboratory
    fields = ['name', 'description', 'location']
    permission_required = 'Laboratory.laboratory_manage'
    template_name = "UdyniManagement/generic_form.html"

    def get_success_url(self):
        return reverse_lazy('lab_and_experimentalstation_view')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Modify laboratory"
        context['back_url'] = self.get_success_url()
        return context

class LaboratoryDelete(PermissionRequiredMixin, DeleteViewMenu):
    model = Laboratory
    permission_required = 'Laboratory.laboratory_manage'
    template_name = "UdyniManagement/confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy('lab_and_experimentalstation_view')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete laboratory"
        context['message'] = f"Are you sure you want to delete the laboratory: {context['laboratory']}?"
        context['back_url'] = self.get_success_url()
        return context


# =============================================
# EXPERIMENTAL STATION
#
class ExperimentalStationCreate(PermissionRequiredMixin, CreateViewMenu):
    model = ExperimentalStation
    fields = ['name', 'description', 'responsible', 'status']  # laboratory is determined when pressing the Add experimental station button inside a lab
    permission_required = 'ExperimentalStation.experimentalstation_manage'
    template_name = "UdyniManagement/generic_form.html"
    
    def form_valid(self, form):
        laboratory_id = self.kwargs['laboratory_id']
        laboratory = get_object_or_404(Laboratory, laboratory_id=laboratory_id)
        form.instance.laboratory = laboratory
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('lab_and_experimentalstation_view')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        laboratory_id = self.kwargs['laboratory_id']
        laboratory = Laboratory.objects.get(laboratory_id=laboratory_id)  # here we must query for the name of the laboratory since it's not in context
        context['title'] = f"Add new experimental station to {laboratory.name}"
        context['back_url'] = self.get_success_url()
        return context

class ExperimentalStationUpdate(PermissionRequiredMixin, UpdateViewMenu):
    model = ExperimentalStation
    fields = ['laboratory', 'name', 'description', 'responsible', 'status']  # here laboratory is present in case is necessary to move an exp station to another lab
    permission_required = 'ExperimentalStation.experimentalstation_manage'
    template_name = "UdyniManagement/generic_form.html"

    def get_success_url(self):
        return reverse_lazy('lab_and_experimentalstation_view')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Modify experimental station"
        context['back_url'] = self.get_success_url()
        return context

class ExperimentalStationDelete(PermissionRequiredMixin, DeleteViewMenu):
    model = ExperimentalStation
    permission_required = 'ExperimentalStation.experimentalstation_manage'
    template_name = "UdyniManagement/confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy('lab_and_experimentalstation_view')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete experimental station"
        context['message'] = f"Are you sure you want to delete the experimental station '{context['experimentalstation'].name}' in lab '{context['experimentalstation'].laboratory}'?"
        context['back_url'] = self.get_success_url()
        return context


# =============================================
# EXPERIMENT FOR EXPERIMENTAL STATION
#
class ExperimentList(PermissionRequiredMixin, ListViewMenu):
    model = Experiment
    permission_required = 'Experiment.experiment_view'

    def get_queryset(self):
        station_id = self.kwargs['station_id']
        return Experiment.objects.filter(experimental_station=station_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        station_id = self.kwargs['station_id']
        station = ExperimentalStation.objects.get(station_id=station_id)  # here we must query for the name of the experimental station since it's not in context
        context['title'] = f"Experiments for {station.name}"
        context['this_station_id'] = station_id  # here the experimental station id is saved so that the urls in the html page can reference to it
        context['can_edit'] = self.request.user.has_perm('Experiment.experiment_manage')
        return context


class ExperimentCreate(PermissionRequiredMixin, CreateViewMenu):
    model = Experiment
    fields = ['project', 'reference', 'description', 'responsible','status']
    permission_required = 'Experiment.experiment_manage'
    template_name = "UdyniManagement/generic_form.html"
    
    def get_success_url(self):
        station_id = self.kwargs['station_id']
        return reverse_lazy('experiment_view', kwargs={'station_id': station_id})
    
    # experimental_station is not editable, it's the same from the web page the experiment has been created
    def form_valid(self, form):
        station_id = self.kwargs['station_id']
        experimental_station = get_object_or_404(ExperimentalStation, station_id=station_id)
        form.instance.experimental_station = experimental_station
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        station_id = self.kwargs['station_id']
        station = ExperimentalStation.objects.get(station_id=station_id)  # here we must query for the name of the experimental station since it's not in context
        context['title'] = f"Add new experiment for {station.name}"
        context['back_url'] = self.get_success_url()
        return context

class ExperimentUpdate(PermissionRequiredMixin, UpdateViewMenu):
    model = Experiment
    fields = ['project', 'reference', 'description', 'responsible','status']
    permission_required = 'Experiment.experiment_manage'
    template_name = "UdyniManagement/generic_form.html"

    def get_success_url(self):
        station_id = self.kwargs['station_id']
        return reverse_lazy('experiment_view', kwargs={'station_id': station_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Modify experiment for {context['experiment'].experimental_station.name}"
        context['back_url'] = self.get_success_url()
        return context

class ExperimentDelete(PermissionRequiredMixin, DeleteViewMenu):
    model = Experiment
    permission_required = 'Experiment.experiment_manage'
    template_name = "UdyniManagement/confirm_delete.html"

    def get_success_url(self):
        station_id = self.kwargs['station_id']
        return reverse_lazy('experiment_view', kwargs={'station_id': station_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete experiment"
        context['message'] = f"Are you sure you want to delete the experiment {context['experiment']}"
        context['back_url'] = self.get_success_url()
        return context


# =============================================
# SAMPLE FOR EXPERIMENT
#
class SampleForExperimentAdd(PermissionRequiredMixin, CreateViewMenu):
    model = SampleForExperiment
    fields = ['sample']
    permission_required = 'Experiment.experiment_manage'
    template_name = "UdyniManagement/generic_form.html"
    
    def get_success_url(self):
        station_id = self.kwargs['station_id']
        return reverse_lazy('experiment_view', kwargs={'station_id': station_id})
    
    def form_valid(self, form):
        experiment_id = self.kwargs['experiment_id']
        experiment = get_object_or_404(Experiment, experiment_id=experiment_id)
        form.instance.experiment = experiment
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experiment_id = self.kwargs['experiment_id']
        experiment = Experiment.objects.get(experiment_id=experiment_id)  # here we must query for the experiment id since it's not in context
        context['title'] = f"Add existing sample to experiement {experiment.experiment_id}"
        context['back_url'] = self.get_success_url()
        return context
    
class SampleForExperimentRemove(PermissionRequiredMixin, DeleteViewMenu):
    model = SampleForExperiment
    permission_required = 'Experiment.experiment_manage'
    template_name = "UdyniManagement/confirm_delete.html"

    def get_success_url(self):
        station_id = self.kwargs['station_id']
        return reverse_lazy('experiment_view', kwargs={'station_id': station_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Remove sample from the experiment"
        context['message'] = f"Are you sure you want to remove the sample '{context['sampleforexperiment'].sample.name}' from the experiment '{context['sampleforexperiment'].experiment.experiment_id}'?"
        context['back_url'] = self.get_success_url()
        return context