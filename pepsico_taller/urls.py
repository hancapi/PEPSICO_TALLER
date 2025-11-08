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

    # Apps
    path('vehiculos/', include('vehiculos.urls', namespace='vehiculos')),
    path('talleres/', include('talleres.urls', namespace='talleres')),
    path('reportes/', include('reportes.urls', namespace='reportes')),
    path('documentos/', include('documentos.urls', namespace='documentos')),

    # APIs
    path('api/autenticacion/', include('autenticacion.urls', namespace='autenticacion')),
    path('api/ordenestrabajo/', include('ordenestrabajo.urls', namespace='ordenestrabajo')),
]

# ✅ Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
