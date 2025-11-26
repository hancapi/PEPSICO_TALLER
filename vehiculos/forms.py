# vehiculos/forms.py
from django import forms
from .models import Vehiculo

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['patente', 'marca', 'modelo', 'anio', 'tipo', 'estado', 'ubicacion']

        widgets = {
            'patente': forms.TextInput(attrs={'class': 'form-control'}),
            'marca':   forms.TextInput(attrs={'class': 'form-control'}),
            'modelo':  forms.TextInput(attrs={'class': 'form-control'}),
            'anio':    forms.NumberInput(attrs={'class': 'form-control'}),

            # 👇 Si en el modelo estos campos tienen `choices`, Django usará <select>
            'tipo':    forms.Select(attrs={'class': 'form-select'}),
            'estado':  forms.Select(attrs={'class': 'form-select'}),

            'ubicacion': forms.Select(attrs={'class': 'form-control'}),
        }