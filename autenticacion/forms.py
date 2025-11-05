# autenticacion/forms.py
from django import forms
from .models import Empleado

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = ['nombre', 'rut', 'cargo', 'region', 'horario', 'disponibilidad', 'usuario']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.Select(attrs={'class': 'form-control'}),  # Cambiado a Select para choices
            'region': forms.Select(attrs={'class': 'form-control'}),  # Cambiado a Select para choices
            'horario': forms.Select(attrs={'class': 'form-control'}),  # Cambiado a Select para choices
            'disponibilidad': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'usuario': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si quieres hacer el last_login de solo lectura cuando se muestre
        # pero como no está en los fields, no aparecerá en tu formulario personalizado