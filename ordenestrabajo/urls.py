from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrdenTrabajoViewSet,
    registrar_orden_trabajo,
    horarios_ocupados  # ✅ Importamos la nueva función
)

app_name = 'ordenestrabajo'

router = DefaultRouter()
router.register(r'ordenestrabajo', OrdenTrabajoViewSet)

urlpatterns = [
    path('registrar/', registrar_orden_trabajo, name='registrar_orden'),
    path('horarios_ocupados/', horarios_ocupados, name='horarios_ocupados'),  # ✅ NUEVA RUTA
    path('', include(router.urls)),
]
