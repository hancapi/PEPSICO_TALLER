# pepsico_taller/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin 
    path('admin/', admin.site.urls),

    # Páginas principales
    path('', TemplateView.as_view(template_name='inicio-sesion.html'), name='home'),
    path('inicio-sesion/', TemplateView.as_view(template_name='inicio-sesion.html'), name='inicio-sesion'),
    path('inicio/', TemplateView.as_view(template_name='inicio.html'), name='inicio'),
    path('registro-taller/', TemplateView.as_view(template_name='registro-taller.html'), name='registro-taller'),
    path('subir-documentos/', TemplateView.as_view(template_name='subir-documentos.html'), name='subir-documentos'),
    path('ingreso-vehiculos/', TemplateView.as_view(template_name='ingreso-vehiculos.html'), name='ingreso-vehiculos'),
    path('ficha-vehiculo/', TemplateView.as_view(template_name='ficha-vehiculo.html'), name='ficha-vehiculo'),
    path('reportes/', TemplateView.as_view(template_name='reportes.html'), name='reportes'),
    path('chat/', include('chat.urls')),   

    # Apps “clásicas”
    path('vehiculos/', include('vehiculos.urls', namespace='vehiculos')),
    path('talleres/', include('talleres.urls', namespace='talleres')),
    path('reportes/', include('reportes.urls', namespace='reportes')),
    path('documentos/', include('documentos.urls', namespace='documentos_html')),  # si tu app ya tiene urls propias para vistas HTML

    # APIs
    path('api/autenticacion/', include('autenticacion.urls', namespace='autenticacion')),
    path('api/ordenestrabajo/', include('ordenestrabajo.urls', namespace='ordenestrabajo')),
    path('api/documentos/', include('documentos.api_urls', namespace='documentos_api')),  # 👈 API de documentos
]

# Servir media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
