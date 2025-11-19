# talleres/urls.py
from django.urls import path
from .views import registro_taller_page
from talleres.views_agenda import agenda_page

app_name = 'talleres'

urlpatterns = [
    path('registro/', registro_taller_page, name='registro_taller'),
    path("agenda/", agenda_page, name="agenda"),
]