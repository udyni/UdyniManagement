from .models import Laboratory, Sample, ExperimentalStation, Experiment, SampleForExperiment, Measurement, File, Comment, CommentContent
from .forms import CommentForm, CommentContentForm
from UdyniManagement.views import ListViewMenu, CreateViewMenu, UpdateViewMenu, DeleteViewMenu
from UdyniManagement.menu import UdyniMenu

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views import View
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render, redirect
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
    fields = ['name', 'material', 'substrate', 'manufacturer', 'description', 'reference']
    permission_required = 'Sample.sample_manage'
    template_name = "UdyniManagement/generic_form.html"
    
    def get_success_url(self):
        return reverse_lazy('sample_view')
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add new sample"
        context['back_url'] = self.get_success_url()
        return context

class SampleUpdate(PermissionRequiredMixin, UpdateViewMenu):
    model = Sample
    fields = ['name', 'material', 'substrate', 'manufacturer', 'description', 'reference']
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
        station = get_object_or_404(ExperimentalStation, station_id=station_id)
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

# =============================================
# EXPERIMENT LOGBOOK
#
def get_comment_tree(experiment):
    return Comment.objects.filter(experiment=experiment).order_by('tree_id', 'lft')


class LogbookList(View):
    http_method_names = ['get']
    template_name = 'LabLogbook/comment_list.html'

    def get(self, request, *args, **kwargs):
        station = get_object_or_404(ExperimentalStation, station_id=kwargs['station_id'])
        experiment = get_object_or_404(Experiment, experiment_id=kwargs['experiment_id'])

        context = {
            'menu': UdyniMenu().getMenu(request.user),
            'title': f"Logbook for experiment {experiment.experiment_id}",
            'back_url' : reverse_lazy('experiment_view', kwargs={'station_id': station.station_id}),
            'back_url_button_title' : f'Experiments for {station.name}',
            'station_id' : station.station_id, # this is used as an argument in various urls in the template
            'experiment_id' : experiment.experiment_id, # this is used as an argument in various urls in the template
            'comment_tree': get_comment_tree(experiment),
        }
        return render(request, self.template_name, context)
    

class CommentContentHistory(View):
    http_method_names = ['get']
    template_name = 'LabLogbook/comment_content_history_list.html'

    def get(self, request, *args, **kwargs):
        station = get_object_or_404(ExperimentalStation, station_id=kwargs['station_id'])
        experiment = get_object_or_404(Experiment, experiment_id=kwargs['experiment_id'])
        comment = get_object_or_404(Comment, comment_id=kwargs['pk'])

        title = f'Content version history for comment {comment.comment_id}'
        # The comment history of deleted comments can be accessed (provided a link) but the user must know that the comment is no more visible
        if comment.latest_content.text == None:
            title += ' (DELETED)'

        context = {
            'menu': UdyniMenu().getMenu(request.user),
            'title': title,
            'back_url' : reverse_lazy('logbook_view', kwargs={'station_id': station.station_id, 'experiment_id': experiment.experiment_id}),
            'back_url_button_title' : f'Logbook for experiment {experiment.experiment_id}',
            'comment': comment,
        }
        return render(request, self.template_name, context)


class CommentCreate(View):
    http_method_names = ['get', 'post']
    template_name = 'LabLogbook/comment_form.html'
    
    def get_experiment_and_back_url(self, **kwargs):
        station = get_object_or_404(ExperimentalStation, station_id=kwargs['station_id'])
        experiment = get_object_or_404(Experiment, experiment_id=kwargs['experiment_id'])
        back_url = reverse_lazy('logbook_view', kwargs={'station_id': station.station_id, 'experiment_id': experiment.experiment_id})
        return experiment, back_url

    def get(self, request, *args, **kwargs):
        experiment, back_url = self.get_experiment_and_back_url(**kwargs)

        comment_form = CommentForm()
        comment_content_form = CommentContentForm()

        context = {
            'menu': UdyniMenu().getMenu(request.user),
            'title': f'Create comment for experiment {experiment.experiment_id}',
            'comment_form': comment_form,
            'comment_content_form': comment_content_form,
            'back_url' : back_url,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        experiment, back_url = self.get_experiment_and_back_url(**kwargs)

        comment_form = CommentForm(request.POST)
        comment_content_form = CommentContentForm(request.POST)
        
        if comment_form.is_valid() and comment_content_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.experiment = experiment
            # measurement, and parent are null when creating a new comment, we don't need to edit them
            comment.save()

            # This instruction is present because when a new tree is created the tree_id of already existing comment could change,
            # this would move entire comment trees in the logbook making the user experience inconsistent, so it's better to have this little overhead.
            # Note that this only applies when a new comment is created, so editing comments does not have any overhead.
            Comment.objects.rebuild()

            comment_content = comment_content_form.save(commit=False)
            comment_content.comment = comment
            comment_content.version = 1
            comment_content.author = self.request.user
            comment_content.save()

            return redirect(back_url)

        context = {
            'menu': UdyniMenu().getMenu(request.user),
            'title': f'Create comment for experiment {experiment.experiment_id}',
            'comment_form': comment_form,
            'comment_content_form': comment_content_form,
            'back_url' : back_url,
        }
        return render(request, self.template_name, context)


class CommentUpdate(View):
    '''
    Type and text of comments can be edited.
    The text can be edited starting from the text of the previous version.

    Note that comments with author = None are machine generated and cannot be edited.

    When a comment text is updated a new entry of comment content is created.
    If text is not changed, it won't be created a new entry of comment content if you press save. You can change the type without creating a new version.
    The new comment inherits the unchanged characteristic from the previous version of comment content, but it has its own author and timestamp.
    '''
    
    http_method_names = ['get', 'post']
    template_name = 'LabLogbook/comment_form.html'
    
    def get_back_url(self, **kwargs):
        station = get_object_or_404(ExperimentalStation, station_id=kwargs['station_id'])
        experiment = get_object_or_404(Experiment, experiment_id=kwargs['experiment_id'])
        return reverse_lazy('logbook_view', kwargs={'station_id': station.station_id, 'experiment_id': experiment.experiment_id})
    
    def get_comment(self, **kwargs):
        return get_object_or_404(Comment, comment_id=kwargs['pk'])

    def get(self, request, *args, **kwargs):
        back_url = self.get_back_url(**kwargs)
        comment = self.get_comment(**kwargs)
        latest_content = comment.latest_content

        initial_comment_form = {
            'type': comment.type,  # get the type currently assigned to the comment
        }
        initial_comment_content_form = {
            'text': latest_content.text, # get the text from the previous version of the comment
        }
        comment_form = CommentForm(initial=initial_comment_form)
        comment_content_form = CommentContentForm(initial=initial_comment_content_form)

        # if the comment is machine generated (has author NULL) it cannot be edited
        machine_generated = True if latest_content.author is None else False
        
        context = {
            'menu': UdyniMenu().getMenu(request.user),
            'title': f"Edit comment {comment.comment_id}",
            'machine_generated': machine_generated,
            'comment_form': comment_form,
            'comment_content_form': comment_content_form,
            'back_url' : back_url,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        back_url = self.get_back_url(**kwargs)
        comment = self.get_comment(**kwargs)
        latest_content = comment.latest_content

        comment_form = CommentForm(request.POST)
        comment_content_form = CommentContentForm(request.POST)

        # if the comment is machine generated (has author NULL) it cannot be edited
        machine_generated = True if latest_content.author is None else False
        
        if comment_form.is_valid() and comment_content_form.is_valid() and not machine_generated:
            # The data gets updated update the the comment and its content, otherwise when save is pressed just go back
            comment_type_inserted_in_form = comment_form.cleaned_data['type']
            if comment_type_inserted_in_form != comment.type:
                # if the type has changed get the object comment and update it
                comment.type = comment_type_inserted_in_form # here i use the value stored in the form in order to update the comment
                comment.save()

            if comment_content_form.cleaned_data['text'] != latest_content.text:
                comment_content = comment_content_form.save(commit=False)
                comment_content.comment = comment  # the referred comment does not change
                comment_content.version = latest_content.version + 1  # update version number
                comment_content.author = self.request.user
                comment_content.save()

            return redirect(back_url)

        context = {
            'menu': UdyniMenu().getMenu(request.user),
            'title': f"Edit comment {comment.comment_id}",
            'machine_generated': machine_generated,
            'comment_form': comment_form,
            'comment_content_form': comment_content_form,
            'back_url' : back_url,
        }
        return render(request, self.template_name, context)


class CommentReply(CreateViewMenu):
    '''
    When replying to a comment a new comment and comment content gets created.
    The new comment has the previous one as its parent.
    '''
    http_method_names = ['get', 'post']
    template_name = 'LabLogbook/comment_reply_form.html'
    
    def get_back_url(self, request, **kwargs):
        station = get_object_or_404(ExperimentalStation, station_id=kwargs['station_id'])
        experiment = get_object_or_404(Experiment, experiment_id=kwargs['experiment_id'])
        back_url = reverse_lazy('logbook_view', kwargs={'station_id': station.station_id, 'experiment_id': experiment.experiment_id})
        return back_url
    
    def get_comment_and_latest_commentcontent(self, request, **kwargs):
        '''
        Used for obtaining the comment to put as parent of the new one and to print
        to screen the comment content the user want to reply to.
        '''
        comment = get_object_or_404(Comment, comment_id=kwargs['pk'])
        # comments are already saved with descendant order of version, no need to order by '-version'
        comment_content = CommentContent.objects.filter(comment=kwargs['pk']).first()
        return comment, comment_content


    def get(self, request, *args, **kwargs):
        comment_to_reply, comment_content_to_reply = self.get_comment_and_latest_commentcontent(request, **kwargs)
        comment_form = CommentForm()
        comment_content_form = CommentContentForm()

        back_url = self.get_back_url(request, **kwargs)
        context = {
            'menu': UdyniMenu().getMenu(request.user),
            'title': f"Reply to comment {comment_to_reply.comment_id}",
            'comment_to_reply' : comment_to_reply,
            'comment_content_to_reply' : comment_content_to_reply,
            'comment_form': comment_form,
            'comment_content_form': comment_content_form,
            'back_url' : back_url,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        comment_to_reply, comment_content_to_reply = self.get_comment_and_latest_commentcontent(request, **kwargs)

        comment_form = CommentForm(request.POST)
        comment_content_form = CommentContentForm(request.POST)
        back_url = self.get_back_url(request, **kwargs)
        
        if comment_form.is_valid() and comment_content_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.experiment = comment_to_reply.experiment
            comment.measurement = comment_to_reply.measurement  # measurment and parent depends on the parent comment
            comment.parent = comment_to_reply
            comment.save()

            comment_content = comment_content_form.save(commit=False)
            comment_content.comment = comment
            comment_content.version = 1
            comment_content.author = self.request.user
            comment_content.save()

            return redirect(back_url)

        context = {
            'menu': UdyniMenu().getMenu(request.user),
            'title': f"Reply to comment {comment_to_reply.comment_id}",
            'comment_form': comment_form,
            'comment_content_form': comment_content_form,
            'back_url' : back_url,
        }
        return render(request, self.template_name, context)

class CommentDelete(CreateViewMenu):
    pass