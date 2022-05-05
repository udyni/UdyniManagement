from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.http import JsonResponse

from django.views import View
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin

from .menu import UdyniMenu


# =============================================
# MAIN INDEX VIEW

class EmptyView(LoginRequiredMixin, View):
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        context = {
            'title': "Welcome!",
            'menu': UdyniMenu().getMenu(request.user),
        }
        return render(request, 'UdyniManagement/page.html', context)


# =============================================
# EXTENDED VIEWS WITH MENU
class ListViewMenu(ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = UdyniMenu().getMenu(self.request.user)
        return context

class CreateViewMenu(CreateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = UdyniMenu().getMenu(self.request.user)
        return context

class UpdateViewMenu(UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = UdyniMenu().getMenu(self.request.user)
        return context

class DeleteViewMenu(DeleteView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = UdyniMenu().getMenu(self.request.user)
        return context
