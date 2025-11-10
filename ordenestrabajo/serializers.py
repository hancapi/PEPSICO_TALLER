#ordenestrabajo/serializers.py
from rest_framework import serializers
from .models import OrdenTrabajo, Repuesto

class RepuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repuesto
        fields = ['repuesto_id', 'cantidad', 'nombre', 'descripcion']

class OrdenTrabajoSerializer(serializers.ModelSerializer):
    repuestos = RepuestoSerializer(many=True, read_only=True, source='repuesto_set')

    class Meta:
        model = OrdenTrabajo
        fields = [
            'ot_id',
            'fecha_ingreso',
            'hora_ingreso',
            'fecha_salida',
            'descripcion',
            'estado',
            'patente',
            'taller',
            'rut',        # ✅ reemplaza "empleado" por "rut"
            'repuestos'
        ]

