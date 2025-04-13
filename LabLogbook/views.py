from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy

from .models import Laboratory, Sample, ExperimentalStation

from django.contrib.auth.mixins import PermissionRequiredMixin

#from .forms import ResearcherRoleForm, ProjectForm

from UdyniManagement.views import ListViewMenu, CreateViewMenu, UpdateViewMenu, DeleteViewMenu


# =============================================
# LABORATORY
#
class LaboratoryList(PermissionRequiredMixin, ListViewMenu):
    model = Laboratory
    permission_required = 'Laboratory.laboratory_view'

    def get_queryset(self):
        return Laboratory.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Laboratories"
        context['can_edit'] = self.request.user.has_perm('Laboratory.laboratory_manage')
        return context

class LaboratoryCreate(PermissionRequiredMixin, CreateViewMenu):
    model = Laboratory
    fields = ['name', 'description', 'location']
    permission_required = 'Laboratory.laboratory_manage'
    template_name = "UdyniManagement/generic_form.html"
    
    def get_success_url(self):
        return reverse_lazy('laboratory_view')
    
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
        return reverse_lazy('laboratory_view')

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
        return reverse_lazy('laboratory_view')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete laboratory"
        context['message'] = "Are you sure you want to delete the laboratory: {0!s}?".format(context['laboratory'])
        context['back_url'] = self.get_success_url()
        return context


# =============================================
# SAMPLE
#
class SampleList(PermissionRequiredMixin, ListViewMenu):
    model = Sample
    permission_required = 'Sample.sample_view'

    def get_queryset(self):
        return Sample.objects.all()

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
        context['message'] = "Are you sure you want to delete the sample: {0!s}?".format(context['sample'])
        context['back_url'] = self.get_success_url()
        return context
    

# =============================================
# SAMPLE
#
class ExperimentalStationList(PermissionRequiredMixin, ListViewMenu):
    model = ExperimentalStation
    permission_required = 'ExperimentalStation.experimentalstation_view'

    def get_queryset(self):
        return ExperimentalStation.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Experimental Stations"
        context['can_edit'] = self.request.user.has_perm('ExperimentalStation.experimentalstation_manage')
        return context

class ExperimentalStationCreate(PermissionRequiredMixin, CreateViewMenu):
    model = ExperimentalStation
    fields = ['laboratory', 'name', 'description', 'responsible', 'status']
    permission_required = 'ExperimentalStation.experimentalstation_manage'
    template_name = "UdyniManagement/generic_form.html"
    
    def get_success_url(self):
        return reverse_lazy('experimentalstation_view')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add new experimental station"
        context['back_url'] = self.get_success_url()
        return context

class ExperimentalStationUpdate(PermissionRequiredMixin, UpdateViewMenu):
    model = ExperimentalStation
    fields = ['name', 'description', 'responsible', 'status']
    permission_required = 'ExperimentalStation.experimentalstation_manage'
    template_name = "UdyniManagement/generic_form.html"

    def get_success_url(self):
        return reverse_lazy('experimentalstation_view')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Modify experimental station in lab " + str(context["experimentalstation"].laboratory)
        context['back_url'] = self.get_success_url()
        return context

class ExperimentalStationDelete(PermissionRequiredMixin, DeleteViewMenu):
    model = ExperimentalStation
    permission_required = 'ExperimentalStation.experimentalstation_manage'
    template_name = "UdyniManagement/confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy('experimentalstation_view')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete experimental station"
        context['message'] = "Are you sure you want to delete the experimental station '{0!s}' in lab '{1!s}'?".format(context["experimentalstation"].name, context["experimentalstation"].laboratory)
        context['back_url'] = self.get_success_url()
        return context