# ordenestrabajo/urls.py
from django.urls import path
from . import views
from . import api_views

app_name = 'ordenestrabajo'

urlpatterns = [

    # ===========================
    # API Mecánico y Supervisor
    # ===========================
    path("mecanico/vehiculos/", api_views.api_mecanico_vehiculos, name="api_mecanico_vehiculos"),
    path("supervisor/vehiculos/", api_views.api_supervisor_vehiculos, name="api_supervisor_vehiculos"),


    # ===========================
    # APIs nuevas (Agenda / Crear OT / Últimas OT / Asignar)
    # ===========================
    path("agenda/slots/", api_views.api_agenda_slots, name="api_agenda_slots"),
    path("ingresos/create/", api_views.api_crear_ingreso, name="api_crear_ingreso"),
    path("ultimas/", api_views.api_ultimas_ot, name="api_ultimas_ot"),
    path("asignar/", api_views.api_asignar_ot, name="api_asignar_ot"),
    


    # ===========================
    # APIs antiguas
    # ===========================
    path('ingresos/en-curso/', views.ingresos_en_curso_api, name='ingresos_en_curso_api'),
    path('ingresos/<int:ot_id>/finalizar/', views.ingreso_finalizar_api, name='ingreso_finalizar_api'),
    path('ingresos/<int:ot_id>/cancelar/', views.ingreso_cancelar_api, name='ingreso_cancelar_api'),
    path("ultimos/", views.api_ultimos_ingresos, name="api_ultimos_ingresos"),
    path('whoami/', views.whoami, name='whoami'),

    # ===========================
    # Pausas
    # ===========================
    path('<int:ot_id>/pausas/start/', views.pausa_start, name='pausa-start'),
    path('<int:ot_id>/pausas/stop/', views.pausa_stop, name='pausa-stop'),
    path('<int:ot_id>/pausas/', views.pausa_list, name='pausa-list'),
]
