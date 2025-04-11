from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy

from .models import Laboratory

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