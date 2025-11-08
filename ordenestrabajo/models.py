from django.db import models
from vehiculos.models import Vehiculo
from autenticacion.models import Empleado
from talleres.models import Taller  # si tienes app talleres

from django.db import models
from vehiculos.models import Vehiculo
from talleres.models import Taller
from autenticacion.models import Empleado  # modelo que usa rut como PK

class OrdenTrabajo(models.Model):
    ot_id = models.AutoField(primary_key=True)
    fecha_ingreso = models.DateField()
    hora_ingreso = models.TimeField(null=True, blank=True)
    fecha_salida = models.DateField(null=True, blank=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    estado = models.CharField(max_length=50, default='Pendiente')

    patente = models.ForeignKey(Vehiculo, db_column='patente', on_delete=models.CASCADE)
    taller = models.ForeignKey(Taller, db_column='taller_id', on_delete=models.CASCADE)
    rut = models.ForeignKey(Empleado, db_column='rut', on_delete=models.CASCADE)

    class Meta:
        db_table = 'ordenestrabajo'
        managed = False  # ⚠️ importante, ya que la tabla ya existe en MySQL


class Repuesto(models.Model):
    repuesto_id = models.AutoField(primary_key=True)
    cantidad = models.IntegerField(default=1)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=500, null=True, blank=True)

    orden_trabajo = models.ForeignKey(
        OrdenTrabajo,
        db_column='ot_id',
        on_delete=models.DO_NOTHING
    )

    class Meta:
        db_table = 'repuestos'
        managed = False
