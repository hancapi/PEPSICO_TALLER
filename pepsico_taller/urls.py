from django.contrib import admin
from django.urls import path, include

# ==========================================================
# ✔ IMPORTS OFICIALES
# ==========================================================
from autenticacion import views_pages                   # login, inicio, ingreso_vehiculos, asignación
from talleres.views import registro_taller_page         # registro taller REAL
from vehiculos.views import ficha_vehiculo              # ficha vehículo REAL
from reportes.views import reportes_page                # reportes REAL

# ❗ IMPORTS OBSOLETOS (QUEDAN COMENTADOS PARA ROLLBACK)
# from autenticacion.views_pages import registro_taller_page   # ← YA NO SE USA
# from autenticacion.views_pages import ficha_vehiculo_page    # ← YA NO SE USA
# from autenticacion.views_pages import reportes_page          # ← YA NO SE USA

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
    # REGISTRO TALLER (OFICIAL – talleres/views.py)
    # ==========================================================
    path('registro-taller/', registro_taller_page, name='registro-taller'),

    # ❗ VERSIÓN ANTIGUA (NO USAR — SOLO REFERENCIA)
    # path('registro-taller/', views_pages.registro_taller_page, name='registro-taller-old'),

    # ==========================================================
    # INGRESO VEHÍCULOS
    # ==========================================================
    path('ingreso-vehiculos/', views_pages.ingreso_vehiculos_page, name='ingreso-vehiculos'),

    # ==========================================================
    # FICHA VEHÍCULO (OFICIAL – vehiculos/views.py)
    # ==========================================================
    path('ficha-vehiculo/', ficha_vehiculo, name='ficha-vehiculo'),

    # ❗ VERSIÓN ANTIGUA (NO USAR)
    # path('ficha-vehiculo/', views_pages.ficha_vehiculo_page, name='ficha-vehiculo-old'),

    # ==========================================================
    # REPORTES (OFICIAL – reportes/views.py)
    # ==========================================================
    path('reportes-dashboard/', reportes_page, name='reportes-dashboard'),

    # ❗ VERSIÓN ANTIGUA (NO USAR)
    # path('reportes-dashboard/', views_pages.reportes_page, name='reportes-dashboard-old'),

    # ==========================================================
    # APPS HTML
    # ==========================================================
    path('chat/', include('chat.urls')),
    path('vehiculos/', include('vehiculos.urls', namespace='vehiculos')),
    path('talleres/', include('talleres.urls', namespace='talleres')),
    path('reportes/', include('reportes.urls', namespace='reportes')),
    path('documentos/', include('documentos.urls', namespace='documentos_html')),

    # ==========================================================
    # APIs
    # ==========================================================
    path('api/ordenestrabajo/', include('ordenestrabajo.urls', namespace='ordenestrabajo')),
    path('api/documentos/', include('documentos.api_urls', namespace='documentos_api')),
    path('api/taller/', include('talleres.urls_api')),

    # ==========================================================
    # ASIGNACIÓN TALLER (OFICIAL)
    # ==========================================================
    path('asignacion-taller/', views_pages.asignacion_taller_page, name='asignacion-taller'),

    # ==========================================================
    # AUTENTICACIÓN
    # ==========================================================
    path('autenticacion/', include('autenticacion.urls')),
]

# MEDIA FILES
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
