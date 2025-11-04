# autenticacion/urls.py
from django.urls import path
from . import views

app_name = 'autenticacion'
urlpatterns = [
    path('status/', views.status_api, name='status_api'),
    path('login/', views.login_api, name='login_api'),
    path('logout/', views.logout_api, name='logout_api'),
    path('dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('registrar/', views.registrar_chofer_api, name='registrar_chofer_api'),
    path('existe/', views.rut_existe_api, name='rut_existe_api'),
]