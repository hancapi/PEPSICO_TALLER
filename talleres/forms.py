# talleres/forms.py
from django import forms
from .models import Recinto, Taller


class BaseBootstrapModelForm(forms.ModelForm):
    """
    ModelForm genérico que aplica clases Bootstrap automáticamente.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            else:
                css = widget.attrs.get("class", "")
                widget.attrs["class"] = (css + " form-control").strip()


class RecintoForm(BaseBootstrapModelForm):
    class Meta:
        model = Recinto
        # No mostramos recinto_id (PK)
        fields = ["nombre", "ubicacion", "jefe_recinto"]


class TallerForm(BaseBootstrapModelForm):
    class Meta:
        model = Taller
        # No mostramos taller_id ni nro_anden (se autogenera en el modelo)
        fields = ["recinto", "encargado_taller"]