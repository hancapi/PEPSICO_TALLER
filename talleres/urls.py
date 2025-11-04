#talleres/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TallerViewSet, registro_taller_view

app_name = 'talleres'

# --- DRF Router ---
router = DefaultRouter()
router.register(r'talleres', TallerViewSet)

urlpatterns = [
    # API
    path('api/', include(router.urls)),
    # Templates
    path('registro/', registro_taller_view, name='registro_taller'),
]