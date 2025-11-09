# documentos/urls.py
from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    path('', views.document_list, name='list'),         # GET ?ot_id=... | ?patente=...
    path('upload/', views.document_upload, name='upload'),  # POST multipart
]
