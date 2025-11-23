# ordenestrabajo/models.py
from django.db import models
from autenticacion.models import Empleado
from vehiculos.models import Vehiculo
from talleres.models import Taller


class OrdenTrabajo(models.Model):
    """
    Representa una OT en el taller.

    Estados:

    - Pendiente   : OT creada y programada, vehículo aún no llega.
    - Recibida    : Vehículo llegó físicamente al taller.
    - En Taller   : Vehículo en proceso (estado legacy / compatibilidad).
    - En Proceso  : Mecánico trabajando activamente.
    - Pausado     : Trabajo detenido (espera, bloqueo, etc.).
    - No Reparable: Se determina que no es reparable.
    - Sin Repuestos: No hay repuestos para continuar.
    - Finalizado  : Trabajo terminado correctamente.
    - Cancelado   : OT cerrada sin ejecución (casos excepcionales).
    """

    class Meta:
        managed = False           # ORM no administra la tabla, viene de BD legacy
        db_table = "ordenestrabajo"

    ESTADO_OT_CHOICES = [
        ("Pendiente", "Pendiente"),
        ("Recibida", "Recibida"),
        ("En Taller", "En Taller"),
        ("En Proceso", "En Proceso"),
        ("Pausado", "Pausado"),
        ("No Reparable", "No Reparable"),   # 👈 finales “negativos”
        ("Sin Repuestos", "Sin Repuestos"), # 👈 finales “negativos”
        ("Finalizado", "Finalizado"),
        ("Cancelado", "Cancelado"),
    ]

    ot_id = models.AutoField(primary_key=True)
    fecha_ingreso = models.DateField()
    hora_ingreso = models.TimeField(null=True, blank=True)
    fecha_salida = models.DateField(null=True, blank=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    estado = models.CharField(
        max_length=50,
        choices=ESTADO_OT_CHOICES,
        default="Pendiente",
    )

    patente = models.ForeignKey(
        Vehiculo,
        db_column="patente",
        to_field="patente",
        on_delete=models.RESTRICT,
    )

    taller = models.ForeignKey(
        Taller,
        db_column="taller_id",
        to_field="taller_id",
        on_delete=models.RESTRICT,
    )

    rut = models.ForeignKey(
        Empleado,
        db_column="rut",
        to_field="rut",
        on_delete=models.RESTRICT,
        related_name="ots_responsable",
    )

    rut_creador = models.ForeignKey(
        Empleado,
        db_column="rut_creador",
        to_field="rut",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ots_creadas",
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


class SolicitudIngresoVehiculo(models.Model):
    ESTADO_CHOICES = (
        ("PENDIENTE", "Pendiente"),
        ("APROBADA", "Aprobada"),
        ("RECHAZADA", "Rechazada"),
        ("CERRADA", "Cerrada"),
    )

    id = models.AutoField(primary_key=True)

    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.PROTECT,
        related_name="solicitudes_ingreso",
    )

    chofer = models.ForeignKey(
        Empleado,
        on_delete=models.PROTECT,
        related_name="solicitudes_ingreso",
    )

    taller = models.ForeignKey(
        Taller,
        on_delete=models.PROTECT,
        related_name="solicitudes_ingreso",
    )

    # Día solicitado por el chofer (SIN hora)
    fecha_solicitada = models.DateField()

    descripcion = models.CharField(max_length=255, blank=True)

    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default="PENDIENTE",
    )

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "solicitudes_ingreso_vehiculo"
        ordering = ["-creado_en"]
        verbose_name = "Solicitud de Ingreso de Vehículo"
        verbose_name_plural = "Solicitudes de Ingreso de Vehículos"

    def __str__(self):
        return f"{self.vehiculo.patente} - {self.fecha_solicitada} ({self.estado})"


class Pausa(models.Model):
    class Meta:
        db_table = "pausas"
        ordering = ["-inicio"]

    ot = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        related_name="pausas",
    )
    motivo = models.CharField(max_length=120)
    observacion = models.TextField(blank=True, default="")
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        estado = "activa" if self.activo else "cerrada"
        return f"Pausa OT {self.ot_id} - {self.ot.patente_id} ({estado})"
