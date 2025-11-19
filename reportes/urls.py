# reportes/urls.py
from django.urls import path
from . import views

app_name = "reportes"

urlpatterns = [
    # Página HTML principal (dashboard con gráficos)
    path('', views.reportes_page, name='reportes'),

    # Página HTML: Reporte de Órdenes de Trabajo (CU07)
    path('ordenes-trabajo/', views.reportes_ot_page, name='reportes_ot'),

    # APIs para dashboard
    path('api/resumen/', views.api_resumen_global, name='api_resumen_global'),
    path('api/talleres/', views.api_resumen_talleres, name='api_resumen_talleres'),
    path('api/tiempos/', views.api_tiempos_promedio, name='api_tiempos_promedio'),

    # APIs para reporte OT (CU07)
    path('api/summary/', views.api_summary, name='api_summary'),
    path('api/ots/', views.api_ots, name='api_ots'),
]
