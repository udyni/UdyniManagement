from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.http import JsonResponse


# =============================================
# MAIN INDEX VIEW

def index(request):
    context = {
        'subtitle': "Welcome!"
    }
    return render(request, 'UdyniManagement/index.html', context)
