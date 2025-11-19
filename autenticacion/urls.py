# autenticacion/urls.py
from django.urls import path
from . import views

app_name = 'autenticacion'

urlpatterns = [

    # ==========================================================
    # 🔹 SALUD DEL SISTEMA
    # ==========================================================
    path('status/', views.status_view, name='status'),

    # ==========================================================
    # 🔹 LOGIN / LOGOUT (API)
    # ==========================================================
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),  # Respuesta JSON

    # ==========================================================
    # 🔹 LOGOUT PARA VISTAS HTML
    # ==========================================================
    path('logout-web/', views.logout_web_view, name='logout-web'),

    # ==========================================================
    # 🔹 KPIs DEL DASHBOARD
    # ==========================================================
    path('dashboard-stats/', views.dashboard_stats_view, name='dashboard-stats'),
]
