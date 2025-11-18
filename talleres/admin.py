# talleres/admin.py
from django.contrib import admin
from .models import Taller


@admin.register(Taller)
class TallerAdmin(admin.ModelAdmin):
    list_display = ('taller_id', 'nombre', 'ubicacion', 'encargado_taller')
    search_fields = ('nombre', 'ubicacion')
    ordering = ('taller_id',)
