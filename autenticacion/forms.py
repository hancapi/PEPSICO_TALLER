# autenticacion/forms.py
from django import forms
from .models import Empleado

class EmpleadoForm(forms.ModelForm):
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
            'recinto',          # 👈 IMPORTANTE: ahora pedimos el recinto
        ]
        widgets = {
            'rut':   forms.TextInput(attrs={'class': 'form-control'}),
            'usuario': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),

            'cargo': forms.Select(attrs={'class': 'form-select'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'horario': forms.Select(attrs={'class': 'form-select'}),

            'disponibilidad': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'recinto': forms.Select(attrs={'class': 'form-select'}),  # FK a Recinto
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # aquí podrías ordenar campos, setear labels, etc. si quieres
