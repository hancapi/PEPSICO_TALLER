# ordenestrabajo/urls.py
from django.urls import path
from . import views
from . import api_views

app_name = 'ordenestrabajo'

urlpatterns = [

    # ======================================================
    # 🆕 SISTEMA — MECÁNICO / SUPERVISOR
    # ======================================================
    path("mecanico/vehiculos/", api_views.api_mecanico_vehiculos, name="api_mecanico_vehiculos"),
    path("supervisor/vehiculos/", api_views.api_supervisor_vehiculos, name="api_supervisor_vehiculos"),

    # Agenda / creación OT / últimas / asignación
    path("agenda/slots/", api_views.api_agenda_slots, name="api_agenda_slots"),
    path("ingresos/create/", api_views.api_crear_ingreso, name="api_crear_ingreso"),
    path("ultimas/", api_views.api_ultimas_ot, name="api_ultimas_ot"),
    path("asignar/", api_views.api_asignar_ot, name="api_asignar_ot"),
]