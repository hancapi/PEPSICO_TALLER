# talleres/urls_api.py
from django.urls import path
from .api_views import api_vehiculos_taller, api_mecanicos_por_taller

urlpatterns = [
    path("vehiculos/", api_vehiculos_taller, name="api_vehiculos_taller"),
    path("mecanicos/", api_mecanicos_por_taller, name="api_mecanicos_por_taller"),
]

