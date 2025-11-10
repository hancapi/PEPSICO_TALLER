# autenticacion/urls.py
from django.urls import path
from . import views

app_name = 'autenticacion'

urlpatterns = [
    # APIs
    path('status/', views.status_view, name='status'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard-stats/', views.dashboard_stats_view, name='dashboard-stats'),
]
