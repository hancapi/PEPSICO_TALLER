# vehiculos/urls.py
from django.urls import path
from . import views

app_name = 'vehiculos'

urlpatterns = [
    # Páginas
    path('ingreso/', views.ingreso_vehiculos, name='ingreso_vehiculos'),
    path('ficha/<str:patente>/', views.ficha_vehiculo, name='ficha_vehiculo'),
    path('ficha/', views.ficha_vehiculo, name='ficha_vehiculo_qs'),  # permite ?patente=ABC123

    # APIs Vehículos
    path('ingresar/', views.ingreso_api, name='ingreso_api'),
    path('existe/', views.existe_vehiculo, name='existe_vehiculo'),

    # APIs Ficha
    path('api/ficha/', views.api_ficha, name='api_ficha'),
    path('api/ficha/ots/', views.api_ficha_ots, name='api_ficha_ots'),
]
