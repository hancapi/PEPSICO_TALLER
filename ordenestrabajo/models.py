# ordenestrabajo/models.py
from django.db import models
from autenticacion.models import Empleado
from vehiculos.models import Vehiculo
from talleres.models import Taller


class OrdenTrabajo(models.Model):
    class Meta:
        managed = False
        db_table = 'ordenestrabajo'

    ESTADO_OT_CHOICES = [
        ("Pendiente", "Pendiente"),
        ("En Proceso", "En Proceso"),
        ("En Taller", "En Taller"),
        ("Finalizado", "Finalizado"),
        ("Cancelado", "Cancelado"),
    ]

    ot_id = models.AutoField(primary_key=True)
    fecha_ingreso = models.DateField()
    hora_ingreso = models.TimeField(null=True, blank=True)
    fecha_salida = models.DateField(null=True, blank=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    estado = models.CharField(max_length=50, choices=ESTADO_OT_CHOICES, default="Pendiente")

    patente = models.ForeignKey(
        Vehiculo,
        db_column='patente',
        to_field='patente',
        on_delete=models.RESTRICT,
    )

    taller = models.ForeignKey(
        Taller,
        db_column='taller_id',
        to_field='taller_id',
        on_delete=models.RESTRICT,
    )

    rut = models.ForeignKey(
        Empleado,
        db_column='rut',
        to_field='rut',
        on_delete=models.RESTRICT,
        related_name='ots_responsable'
    )

    rut_creador = models.ForeignKey(
        Empleado,
        db_column='rut_creador',
        to_field='rut',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ots_creadas'
    )

    # ======================================================
    # Normalización para que nunca falle por KG.JV93 etc.
    # ======================================================
    def save(self, *args, **kwargs):
        if self.patente_id:
            self.patente_id = (
                self.patente_id.replace(".", "")
                                .replace("-", "")
                                .strip()
                                .upper()
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OT #{self.ot_id} - {self.patente_id} ({self.estado})"


class Repuesto(models.Model):
    class Meta:
        managed = False
        db_table = 'repuestos'

    repuesto_id = models.AutoField(primary_key=True)
    cantidad = models.IntegerField(default=1)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=500, null=True, blank=True)

    ot = models.ForeignKey(
        OrdenTrabajo,
        db_column='ot_id',
        to_field='ot_id',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.nombre} x{self.cantidad} (OT {self.ot_id})"


class Incidente(models.Model):
    class Meta:
        managed = False
        db_table = 'incidentes'

    incidente_id = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(null=True, blank=True)
    descripcion = models.CharField(max_length=1000)
    patente = models.ForeignKey(Vehiculo, db_column='patente', on_delete=models.RESTRICT)
    rut = models.ForeignKey(Empleado, db_column='rut', to_field='rut', on_delete=models.RESTRICT)

    def __str__(self):
        return f"Incidente {self.incidente_id} - {self.patente_id}"


class PrestamoVehiculo(models.Model):
    class Meta:
        managed = False
        db_table = 'prestamosvehiculos'

    ESTADO_PRESTAMO_CHOICES = [
        ("En uso", "En uso"),
        ("Devuelto", "Devuelto"),
        ("Retrasado", "Retrasado"),
    ]

    prestamo_id = models.AutoField(primary_key=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=50, choices=ESTADO_PRESTAMO_CHOICES, default="En uso")
    patente = models.ForeignKey(Vehiculo, db_column='patente', on_delete=models.RESTRICT)
    empleados_rut = models.ForeignKey(Empleado, db_column='empleados_rut', to_field='rut', on_delete=models.RESTRICT)

    def __str__(self):
        return f"Préstamo {self.prestamo_id} - {self.patente_id}"


class Llave(models.Model):
    class Meta:
        managed = False
        db_table = 'llaves'

    ESTADO_LLAVE_CHOICES = [
        ("Disponible", "Disponible"),
        ("Prestada", "Prestada"),
        ("Extraviada", "Extraviada"),
    ]

    llave_id = models.AutoField(primary_key=True)
    estado = models.CharField(max_length=50, choices=ESTADO_LLAVE_CHOICES, default="Disponible")

    rut = models.ForeignKey(
        Empleado,
        db_column='rut',
        to_field='rut',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    patente = models.ForeignKey(Vehiculo, db_column='patente', on_delete=models.RESTRICT)

    def __str__(self):
        return f"Llave {self.llave_id} - {self.patente_id}"


class Pausa(models.Model):
    class Meta:
        db_table = 'pausas'
        ordering = ['-inicio']

    ot = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE, related_name='pausas')
    motivo = models.CharField(max_length=120)
    observacion = models.TextField(blank=True, default='')
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        estado = 'activa' if self.activo else 'cerrada'
        return f"Pausa OT {self.ot_id} - {self.ot.patente_id} ({estado})"
