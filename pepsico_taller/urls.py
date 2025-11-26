from django.contrib import admin
from django.urls import path, include

# ==========================================================
# ✔ IMPORTS OFICIALES (CORRECTOS)
# ==========================================================
from autenticacion import views_pages                   # login, inicio, ingreso_vehiculos, asignación
from talleres.views import registro_taller_page         # registro taller REAL
from vehiculos.views import ficha_vehiculo              # ficha vehículo REAL
from reportes.views import reportes_page                # reportes REAL
from ordenestrabajo.views_control_acceso import control_acceso_guardia
from autenticacion.views_pages import control_acceso_page

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # ==========================================================
    # LOGIN / LOGOUT
    # ==========================================================
    path('', views_pages.login_page, name='home'),
    path('inicio-sesion/', views_pages.login_page, name='inicio-sesion'),

    # ==========================================================
    # DASHBOARD PRINCIPAL
    # ==========================================================
    path('inicio/', views_pages.inicio_page, name='inicio'),

    # ==========================================================
    # REGISTRO TALLER — (OFICIAL – talleres/views.py)
    # ==========================================================
    path('registro-taller/', registro_taller_page, name='registro-taller'),

    # ==========================================================
    # INGRESO VEHÍCULOS
    # ==========================================================
    path('ingreso-vehiculos/', views_pages.ingreso_vehiculos_page, name='ingreso-vehiculos'),

    # ==========================================================
    # FICHA VEHÍCULO — (OFICIAL – vehiculos/views.py)
    # ==========================================================
    path('ficha-vehiculo/', ficha_vehiculo, name='ficha-vehiculo'),

    # ==========================================================
    # REPORTES — (OFICIAL – reportes/views.py)
    # ==========================================================
    path('reportes-dashboard/', reportes_page, name='reportes-dashboard'),

    # ==========================================================
    # APPS HTML
    # ==========================================================
    path('chat/', include('chat.urls')),
    path('vehiculos/', include('vehiculos.urls', namespace='vehiculos')),
    path('talleres/', include('talleres.urls', namespace='talleres')),
    path('reportes/', include('reportes.urls', namespace='reportes')),

    # ==========================================================
    # APIs
    # ==========================================================
    path('api/ordenestrabajo/', include('ordenestrabajo.urls', namespace='ordenestrabajo')),
    path('api/documentos/', include('documentos.urls', namespace='documentos')),
    path('api/taller/', include('talleres.urls_api')),
    
    # ==========================================================
    # ASIGNACIÓN TALLER — (OFICIAL)
    # ==========================================================
    path('asignacion-taller/', views_pages.asignacion_taller_page, name='asignacion-taller'),

    # ==========================================================
    # AUTENTICACIÓN
    # ==========================================================
    path('autenticacion/', include('autenticacion.urls')),
    path("control-acceso/", control_acceso_guardia, name="control-acceso"),
    path("control-acceso/", control_acceso_page, name="control-acceso"),

]


# ==========================================================
# SERVIR ARCHIVOS MEDIA EN DEBUG
# ==========================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
