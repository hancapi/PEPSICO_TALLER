#ordenestrabajo/models.py
from django.db import models

class OrdenTrabajo(models.Model):
    ot_id = models.AutoField(primary_key=True)
    fecha_ingreso = models.DateField()
    hora_ingreso = models.TimeField()
    fecha_salida = models.DateField(null=True, blank=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    estado = models.CharField(max_length=50, default='Pendiente')

    patente = models.ForeignKey('vehiculos.Vehiculo', db_column='patente', on_delete=models.DO_NOTHING)
    taller = models.ForeignKey('talleres.Taller', db_column='taller_id', on_delete=models.DO_NOTHING)
    empleado = models.ForeignKey('autenticacion.Empleado', db_column='rut', to_field='rut', on_delete=models.DO_NOTHING)

    class Meta:
        db_table = 'ordenestrabajo'
        managed = False


class Repuesto(models.Model):
    repuesto_id = models.AutoField(primary_key=True)
    cantidad = models.IntegerField()
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)

    orden_trabajo = models.ForeignKey('OrdenTrabajo', db_column='ot_id', on_delete=models.DO_NOTHING)

    class Meta:
        db_table = 'repuestos'
        managed = False

