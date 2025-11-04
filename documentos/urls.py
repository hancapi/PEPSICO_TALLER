from django.urls import path
from django.views.generic import TemplateView

app_name = 'documentos'

urlpatterns = [
    path('subir/', TemplateView.as_view(template_name='subir-documentos.html'), name='subir_documentos'),
]