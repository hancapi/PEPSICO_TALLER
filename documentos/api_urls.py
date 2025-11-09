# documentos/api_urls.py
from django.urls import path
from . import api_views

app_name = 'documentos_api'

urlpatterns = [
    path('', api_views.document_list, name='list'),          # GET ?ot_id=... | ?patente=...
    path('upload/', api_views.document_upload, name='upload') # POST multipart
]
