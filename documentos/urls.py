from django.urls import path
from . import api_views

app_name = 'documentos_api'

urlpatterns = [
    path('', api_views.api_documentos_list, name='list'),
    path('upload/', api_views.api_documentos_upload, name='upload'),
]
