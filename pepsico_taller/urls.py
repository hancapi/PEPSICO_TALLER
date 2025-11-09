# pepsico_taller/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Páginas principales
    path('', TemplateView.as_view(template_name='inicio.html'), name='home'),
    path('inicio/', TemplateView.as_view(template_name='inicio.html'), name='inicio'),

    # Login / Logout reales
    path('inicio-sesion/', auth_views.LoginView.as_view(template_name='inicio-sesion.html'), name='inicio-sesion'),
    path('salir/', auth_views.LogoutView.as_view(), name='logout'),

    # Apps
    path('vehiculos/', include(('vehiculos.urls', 'vehiculos'), namespace='vehiculos')),
    path('talleres/', include(('talleres.urls', 'talleres'), namespace='talleres')),
    path('reportes/', include(('reportes.urls', 'reportes'), namespace='reportes')),
    path('documentos/', include(('documentos.urls', 'documentos'), namespace='documentos')),

    # APIs
    path('api/autenticacion/', include(('autenticacion.urls', 'autenticacion'), namespace='autenticacion')),
    path('api/ordenestrabajo/', include(('ordenestrabajo.urls', 'ordenestrabajo'), namespace='ordenestrabajo')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
