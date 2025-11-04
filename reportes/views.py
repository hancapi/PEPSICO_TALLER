from django.shortcuts import render

# reportes/views.py
from django.shortcuts import render
from django.http import HttpResponse

def reporte_inicio(request):
    return HttpResponse("Página de reportes funcionando")

