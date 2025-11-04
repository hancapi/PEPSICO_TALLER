#vehiculos/forms.py
from django import forms
from .models import Vehiculo
from autenticacion.models import Empleado
from talleres.models import Taller

# Opciones para disponibilidad
DISPONIBILIDAD_CHOICES = [
    (1, 'Disponible'),
    (0, 'No Disponible'),
]

class VehiculoForm(forms.ModelForm):
    cargo = forms.ChoiceField(choices=[], required=True)
    region = forms.ChoiceField(choices=[], required=True)
    horario = forms.ChoiceField(choices=[], required=True)
    disponibilidad = forms.ChoiceField(choices=DISPONIBILIDAD_CHOICES, required=True)
    ubicacion = forms.ModelChoiceField(
        queryset=Taller.objects.all(),
        empty_label="Seleccione un taller",
        required=True
    )

    class Meta:
        model = Vehiculo
        fields = ['patente', 'marca', 'modelo', 'anio', 'tipo', 'estado', 'ubicacion']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            empleados = Empleado.objects.all()
            cargos = [(e['cargo'], e['cargo']) for e in empleados.values('cargo').distinct()]
            regiones = [(e['region'], e['region']) for e in empleados.values('region').distinct()]
            horarios = [(e['horario'], e['horario']) for e in empleados.values('horario').distinct()]

            self.fields['cargo'].choices = cargos
            self.fields['region'].choices = regiones
            self.fields['horario'].choices = horarios
        except Exception:
            self.fields['cargo'].choices = []
            self.fields['region'].choices = []
            self.fields['horario'].choices = []
