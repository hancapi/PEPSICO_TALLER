# reportes/urls.py
from django.urls import path
from . import views

app_name = "reportes"

urlpatterns = [
    # Página HTML principal
    path('', views.reportes_page, name='reportes'),

    # APIs EXISTENTES
    path('api/resumen/', views.api_resumen_global, name='api_resumen_global'),
    path('api/talleres/', views.api_resumen_talleres, name='api_resumen_talleres'),
    path('api/tiempos/', views.api_tiempos_promedio, name='api_tiempos_promedio'),

    # APIs NUEVAS (que tu JS espera)
    path('api/summary/', views.api_summary, name='api_summary'),
    path('api/ots/', views.api_ots, name='api_ots'),
]
