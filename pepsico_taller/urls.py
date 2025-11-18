from django.contrib import admin
from django.urls import path, include
from autenticacion import views_pages 
from talleres.views import registro_taller_page   # <-- ✔️ IMPORT NUEVO
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # PÁGINA PÚBLICA (login)
    path('', views_pages.login_page, name='home'),
    path('inicio-sesion/', views_pages.login_page, name='inicio-sesion'),

    # PÁGINAS PROTEGIDAS
    path('inicio/', views_pages.inicio_page, name='inicio'),
    path('registro-taller/', registro_taller_page, name='registro-taller'),  # <-- ✔️ ARREGLADO
    path('ingreso-vehiculos/', views_pages.ingreso_vehiculos_page, name='ingreso-vehiculos'),
    path('ficha-vehiculo/', views_pages.ficha_vehiculo_page, name='ficha-vehiculo'),
    path('reportes-dashboard/', views_pages.reportes_page, name='reportes-dashboard'),

    # APPS HTML
    path('chat/', include('chat.urls')),
    path('vehiculos/', include('vehiculos.urls', namespace='vehiculos')),
    path('talleres/', include('talleres.urls', namespace='talleres')),
    path('reportes/', include('reportes.urls', namespace='reportes')),
    path('documentos/', include('documentos.urls', namespace='documentos_html')),

    # APIs
    path('api/ordenestrabajo/', include('ordenestrabajo.urls', namespace='ordenestrabajo')),
    path('api/documentos/', include('documentos.api_urls', namespace='documentos_api')),
    path('api/taller/', include('talleres.urls_api')),
    path('asignacion-taller/', views_pages.asignacion_taller_page, name='asignacion-taller'),


    # AUTENTICACIÓN
    path('autenticacion/', include('autenticacion.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
