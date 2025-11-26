# autenticacion/urls.py
from django.urls import path
from . import views
from autenticacion import views_pages

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

    # ==========================================================
    # 🔹 ADMIN WEB – HOME
    # ==========================================================
    path('admin-web/', views_pages.admin_web_panel_page, name='admin-web'),

    # ==========================================================
    # 🔹 ADMIN WEB – VEHÍCULOS
    # ==========================================================
    path(
        'admin-web/vehiculos/',
        views_pages.admin_web_vehiculos_page,
        name='admin-web-vehiculos',
    ),
    path(
        'admin-web/vehiculos/nuevo/',
        views_pages.admin_web_vehiculo_create,
        name='admin-web-vehiculo-nuevo',
    ),
    path(
        'admin-web/vehiculos/<str:patente>/editar/',
        views_pages.admin_web_vehiculo_edit,
        name='admin-web-vehiculo-editar',
    ),
    path(
        'admin-web/vehiculos/<str:patente>/eliminar/',
        views_pages.admin_web_vehiculo_delete,
        name='admin-web-vehiculo-eliminar',
    ),

    # ==========================================================
    # 🔹 ADMIN WEB – EMPLEADOS
    # ==========================================================
    path(
        'admin-web/empleados/',
        views_pages.admin_web_empleados_page,
        name='admin-web-empleados',
    ),
    path(
        'admin-web/empleados/nuevo/',
        views_pages.admin_web_empleado_create,
        name='admin-web-empleado-nuevo',
    ),
    path(
        'admin-web/empleados/<str:rut>/editar/',
        views_pages.admin_web_empleado_edit,
        name='admin-web-empleado-editar',
    ),
    path(
        'admin-web/empleados/<str:rut>/eliminar/',
        views_pages.admin_web_empleado_delete,
        name='admin-web-empleado-eliminar',
    ),

    # ==========================================================
    # 🔹 ADMIN WEB – RECINTOS (CRUD)
    # ==========================================================
    path(
        'admin-web/recintos/',
        views_pages.admin_web_recintos_page,
        name='admin-web-recintos',
    ),
    path(
        'admin-web/recintos/nuevo/',
        views_pages.admin_web_recinto_create,
        name='admin-web-recinto-nuevo',
    ),
    path(
        'admin-web/recintos/<int:pk>/editar/',
        views_pages.admin_web_recinto_edit,
        name='admin-web-recinto-editar',
    ),
    path(
        'admin-web/recintos/<int:pk>/eliminar/',
        views_pages.admin_web_recinto_delete,
        name='admin-web-recinto-eliminar',
    ),

    # ==========================================================
    # 🔹 ADMIN WEB – TALLERES (CRUD)
    # ==========================================================
    path(
        'admin-web/talleres/',
        views_pages.admin_web_talleres_page,
        name='admin-web-talleres',
    ),
    path(
        'admin-web/talleres/nuevo/',
        views_pages.admin_web_taller_create,
        name='admin-web-taller-nuevo',
    ),
    path(
        'admin-web/talleres/<int:pk>/editar/',
        views_pages.admin_web_taller_edit,
        name='admin-web-taller-editar',
    ),
    path(
        'admin-web/talleres/<int:pk>/eliminar/',
        views_pages.admin_web_taller_delete,
        name='admin-web-taller-eliminar',
    ),
]
