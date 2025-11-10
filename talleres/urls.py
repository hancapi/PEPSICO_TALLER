# talleres/urls.py
from django.urls import path
from . import views

app_name = "talleres"

urlpatterns = [
    path("registro/", views.registro_taller, name="registro_taller"),
]
