# autenticacion/forms.py
from django import forms
from django.contrib.auth.models import User, Group
from .models import Empleado


class EmpleadoForm(forms.ModelForm):
    # Campo extra, NO existe en la tabla MySQL
    es_admin_web = forms.BooleanField(
        required=False,
        label="Administrador Web",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Puede acceder al panel de Administración Web.",
    )

    class Meta:
        model = Empleado
        fields = [
            'rut',
            'usuario',
            'nombre',
            'cargo',
            'region',
            'horario',
            'disponibilidad',
            'recinto',
            # es_admin_web NO va aquí porque no es campo de modelo
        ]
        widgets = {
            'rut':   forms.TextInput(attrs={'class': 'form-control'}),
            'usuario': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),

            'cargo': forms.Select(attrs={'class': 'form-select'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'horario': forms.Select(attrs={'class': 'form-select'}),

            'disponibilidad': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'recinto': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Inicializar checkbox según grupo ADMIN_WEB del usuario vinculado
        instance: Empleado = self.instance
        user = instance.linked_user if instance.pk else None
        if user and user.groups.filter(name='ADMIN_WEB').exists():
            self.fields['es_admin_web'].initial = True

    def save(self, commit=True):
        # Primero guardamos el empleado
        empleado: Empleado = super().save(commit=commit)

        # Aseguramos que exista un User vinculado
        user = empleado.linked_user
        if not user:
            user = User(
                username=empleado.usuario,
                email=empleado.email,
                is_active=empleado.is_active,
            )
            # No definimos password aquí (no se usará para login directo)
            user.set_unusable_password()
            user.save()

        # Gestionar grupo ADMIN_WEB según el checkbox
        want_admin = self.cleaned_data.get('es_admin_web', False)
        admin_group, _ = Group.objects.get_or_create(name='ADMIN_WEB')

        if want_admin:
            user.groups.add(admin_group)
        else:
            user.groups.remove(admin_group)

        # staff si es SUPERVISOR o si es admin web
        is_supervisor = user.groups.filter(name='SUPERVISOR').exists()
        user.is_staff = is_supervisor or want_admin
        user.save()

        return empleado
