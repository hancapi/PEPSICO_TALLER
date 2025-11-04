#autenticacion/forms.py
from django import forms
from .models import Empleado

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = ['nombre', 'rut', 'cargo', 'region', 'horario', 'disponibilidad', 'usuario']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.TextInput(attrs={'class': 'form-control'}),
            'horario': forms.TextInput(attrs={'class': 'form-control'}),
            'disponibilidad': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'usuario': forms.TextInput(attrs={'class': 'form-control'}),
        }
