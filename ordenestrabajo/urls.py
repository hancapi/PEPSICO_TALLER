# ordenestrabajo/urls.py
from django.urls import path
from . import views

app_name = 'ordenestrabajo'

urlpatterns = [
    path('<int:ot_id>/pausas/start/', views.pausa_start, name='pausa-start'),
    path('<int:ot_id>/pausas/stop/', views.pausa_stop, name='pausa-stop'),
    path('<int:ot_id>/pausas/', views.pausa_list, name='pausa-list'),
]
