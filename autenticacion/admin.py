# autenticacion/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Empleado

@admin.register(Empleado)
class EmpleadoAdmin(UserAdmin):
    model = Empleado
    list_display = ('rut', 'usuario', 'nombre', 'cargo', 'region', 'is_active', 'is_staff')
    search_fields = ('rut', 'usuario', 'nombre')
    ordering = ('rut',)
    
    # ✅ SOLUCIÓN: Agregar esta línea
    readonly_fields = ('last_login',)

    fieldsets = (
        (None, {'fields': ('rut', 'usuario', 'password')}),
        ('Información personal', {'fields': ('nombre', 'cargo', 'region', 'horario', 'disponibilidad', 'taller')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('rut', 'usuario', 'password1', 'password2', 'nombre', 'cargo', 'region', 'taller', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )
