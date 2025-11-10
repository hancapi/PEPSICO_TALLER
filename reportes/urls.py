# reportes/urls.py
from django.urls import path
from . import views

app_name = 'reportes'
urlpatterns = [
    path('', views.reportes_page, name='reportes'),
    path('api/summary/', views.api_summary, name='api_summary'),
    path('api/ots/', views.api_ots, name='api_ots'),
]
