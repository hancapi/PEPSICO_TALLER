#vehiculos/urls.py
from django.urls import path
from django.views.generic import TemplateView
from .views import ingreso_vehiculos_view, ingreso_api, existe_vehiculo

app_name = 'vehiculos'

urlpatterns = [
    path('ingreso/', ingreso_vehiculos_view, name='ingreso_vehiculos'),
    path('ingresar/', ingreso_api, name='ingreso_api'),
    path('existe/', existe_vehiculo, name='existe_vehiculo'),
]