from django.urls import path
from . import views

app_name = 'ordenestrabajo'

urlpatterns = [
    # Pausas
    path('<int:ot_id>/pausas/start/', views.pausa_start, name='pausa-start'),
    path('<int:ot_id>/pausas/stop/', views.pausa_stop, name='pausa-stop'),
    path('<int:ot_id>/pausas/', views.pausa_list, name='pausa-list'),

    # Agenda / Ingresos
    path('api/agenda/slots/', views.agenda_slots_api, name='agenda_slots_api'),
    path('api/ingresos/create/', views.ingreso_create_api, name='ingreso_create_api'),
    path('api/ingresos/en-curso/', views.ingresos_en_curso_api, name='ingresos_en_curso_api'),
    path('api/ingresos/<int:ot_id>/finalizar/', views.ingreso_finalizar_api, name='ingreso_finalizar_api'),
    path('api/ingresos/<int:ot_id>/cancelar/', views.ingreso_cancelar_api, name='ingreso_cancelar_api'),

    # whoami (para mostrar rut/usuario autenticado en el front)
    path('api/whoami/', views.whoami, name='whoami'),
]

