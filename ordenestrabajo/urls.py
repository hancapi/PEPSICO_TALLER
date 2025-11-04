#ordenestrabajo/urls.py
from django.urls import path
from .views import registrar_ingreso, OrdenTrabajoViewSet, horarios_ocupados
from rest_framework.routers import DefaultRouter

app_name = 'ordenestrabajo'

router = DefaultRouter()
router.register(r'ordenestrabajo', OrdenTrabajoViewSet)

urlpatterns = router.urls + [
    path('horarios/', horarios_ocupados, name='horarios_ocupados'),
    path('registrar/', registrar_ingreso, name='registrar_ingreso'),
]
