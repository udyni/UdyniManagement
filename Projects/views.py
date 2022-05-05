from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.db.models import F

from .models import Researcher, ResearcherRole, Project, WorkPackage

from django.contrib.auth.mixins import PermissionRequiredMixin

from .forms import ResearcherRoleForm, ProjectForm

from django.views import View
from UdyniManagement.views import ListViewMenu, CreateViewMenu, UpdateViewMenu, DeleteViewMenu


# =============================================
# RESEARCHERS VIEWS

class ResearcherList(PermissionRequiredMixin, ListViewMenu):
    model = Researcher
    permission_required = 'reporting.read'

    def get_queryset(self):
        return Researcher.objects.all().annotate(user=F("username__username")).order_by('surname', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Researchers"
        researchers = list(context['researcher_list'].values())
        for r in researchers:
            r['roles'] = ResearcherRole.objects.filter(researcher=r['id'])
        context['researcher_list'] = researchers
        return context


class ResearcherCreate(PermissionRequiredMixin, CreateViewMenu):
    model = Researcher
    fields = ['name', 'surname', 'username']
    success_url = reverse_lazy('researcher_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/generic_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add new researcher"
        context['back_url'] = 'researcher_view'
        return context


class ResearcherUpdate(PermissionRequiredMixin, UpdateViewMenu):
    model = Researcher
    fields = ['name', 'surname', 'username']
    success_url = reverse_lazy('researcher_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/generic_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Modify researcher"
        context['back_url'] = 'researcher_view'
        return context


class ResearcherDelete(PermissionRequiredMixin, DeleteViewMenu):
    model = Researcher
    success_url = reverse_lazy('researcher_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete researcher"
        context['message'] = "Are you sure you want to delete the researcher: {0!s}?".format(context['researcher'])
        context['back_url'] = 'researcher_view'
        return context


class ResearcherRoleCreate(PermissionRequiredMixin, CreateViewMenu):
    model = ResearcherRole
    form_class = ResearcherRoleForm
    success_url = reverse_lazy('researcher_view')
    permission_required = 'reporting.modify'

    def get_initial(self):
        return {'researcher': self.kwargs['researcher']}

    def get_context_data(self, **kwargs):
        r = get_object_or_404(Researcher, pk=self.kwargs['researcher'])
        context = super().get_context_data(**kwargs)
        context['title'] = "Add new role for {0!s}".format(r)
        context['researcher'] = r
        context['back_url'] = 'researcher_view'
        return context


class ResearcherRoleUpdate(PermissionRequiredMixin, UpdateViewMenu):
    model = ResearcherRole
    success_url = reverse_lazy('researcher_view')
    form_class = ResearcherRoleForm
    permission_required = 'reporting.modify'

    def get_context_data(self, **kwargs):
        r = get_object_or_404(Researcher, pk=self.kwargs['researcher'])
        context = super().get_context_data(**kwargs)
        context['title'] = "Modify role for {0!s}".format(r)
        context['researcher'] = r
        context['back_url'] = 'researcher_view'
        return context


class ResearcherRoleDelete(PermissionRequiredMixin, DeleteViewMenu):
    model = ResearcherRole
    success_url = reverse_lazy('researcher_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/confirm_delete.html"

    def get_context_data(self, **kwargs):
        r = get_object_or_404(Researcher, pk=self.kwargs['researcher'])
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete role for {0!s}".format(r)
        context['message'] = "Are you sure you want to delete role {0!s} for researcher {1!s}?".format(context['researcherrole'], r)
        context['back_url'] = 'researcher_view'
        return context


# =============================================
# PROJECTS and WORKPACKAGES
#
class ProjectList(PermissionRequiredMixin, ListViewMenu):
    model = Project
    permission_required = 'reporting.read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Projects & Work Packages"
        return context


class ProjectCreate(PermissionRequiredMixin, CreateViewMenu):
    model = Project
    form_class = ProjectForm
    success_url = reverse_lazy('project_view')
    permission_required = 'reporting.modify'
    template_name = "Projects/project_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add new project"
        context['back_url'] = 'project_view'
        return context


class ProjectUpdate(PermissionRequiredMixin, UpdateViewMenu):
    model = Project
    form_class = ProjectForm
    success_url = reverse_lazy('project_view')
    permission_required = 'reporting.modify'
    template_name = "Projects/project_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Modify project"
        context['back_url'] = 'project_view'
        return context


class ProjectDelete(PermissionRequiredMixin, DeleteViewMenu):
    model = Project
    success_url = reverse_lazy('project_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete project"
        context['message'] = "Are you sure you want to delete project {0!s}?".format(context['project'])
        context['back_url'] = 'project_view'
        return context


class ProjectGaeRedirect(PermissionRequiredMixin, View):
    permission_required = 'reporting.modify'
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        prj = get_object_or_404(Project, pk=self.kwargs['pk'])
        return redirect('sigla_gae', pg_progetto=prj.sigla_id)


# =============================================
# Work packages
#
class WorkPackageCreate(PermissionRequiredMixin, CreateViewMenu):
    model = WorkPackage
    fields = ['name', 'desc']
    success_url = reverse_lazy('project_view')
    permission_required = 'reporting.read'
    template_name = "UdyniManagement/generic_form.html"

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['project'])
        form.instance.project = project
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, pk=self.kwargs['project'])
        context['title'] = "Add new work package to project " + str(project)
        context['back_url'] = 'project_view'
        return context


class WorkPackageUpdate(PermissionRequiredMixin, UpdateViewMenu):
    model = WorkPackage
    fields = ['name', 'desc']
    success_url = reverse_lazy('project_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/generic_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Modify work package of project " + str(context['workpackage'].project)
        context['back_url'] = 'project_view'
        return context


class WorkPackageDelete(DeleteViewMenu):
    model = WorkPackage
    success_url = reverse_lazy('project_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete work package of project " + str(context['workpackage'].project)
        context['message'] = "Are you sure you want to delete the workpackage {0!s} in project {1!s}?".format(context['workpackage'].name, context['workpackage'].project)
        context['back_url'] = 'project_view'
        return context
