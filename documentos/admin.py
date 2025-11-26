# documentos/admin.py
from django.contrib import admin
from .models import Documento


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'tipo', 'ot', 'patente', 'creado_en')
    list_filter = ('tipo', 'creado_en')
    search_fields = ('titulo', 'ot__ot_id', 'patente__patente')
    ordering = ('-creado_en',)
