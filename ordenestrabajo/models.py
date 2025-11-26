# ordenestrabajo/models.py
from django.db import models

from autenticacion.models import Empleado
from vehiculos.models import Vehiculo
from talleres.models import Taller, Recinto


class OrdenTrabajo(models.Model):
    """
    Representa una OT en el taller / recinto.

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
        managed = False           # ORM no administra la tabla, viene de BD
        db_table = "ordenestrabajo"

    ESTADO_OT_CHOICES = [
        ("Pendiente", "Pendiente"),
        ("Recibida", "Recibida"),
        ("En Taller", "En Taller"),
        ("En Proceso", "En Proceso"),
        ("Pausado", "Pausado"),
        ("No Reparable", "No Reparable"),
        ("Sin Repuestos", "Sin Repuestos"),
        ("Finalizado", "Finalizado"),
        ("Cancelado", "Cancelado"),
    ]

    ot_id = models.AutoField(primary_key=True)
    fecha_ingreso = models.DateField()
    hora_ingreso = models.TimeField(null=True, blank=True)
    fecha_salida = models.DateField(null=True, blank=True)

    # ⬅️ Alineado con la BD: VARCHAR(2000) para bitácora / comentarios
    descripcion = models.CharField(max_length=2000, null=True, blank=True)

    estado = models.CharField(
        max_length=50,
        choices=ESTADO_OT_CHOICES,
        default="Pendiente",
    )

    # 🔹 La OT cuelga del RECINTO (recinto_id en la tabla)
    recinto = models.ForeignKey(
        Recinto,
        db_column="recinto_id",
        to_field="recinto_id",
        on_delete=models.RESTRICT,
        related_name="ordenes_trabajo",
    )

    patente = models.ForeignKey(
        Vehiculo,
        db_column="patente",
        to_field="patente",
        on_delete=models.RESTRICT,
    )

    # Empleado responsable de la OT (mecánico)
    rut = models.ForeignKey(
        Empleado,
        db_column="rut",
        to_field="rut",
        on_delete=models.RESTRICT,
        related_name="ots_responsable",
    )

    # Empleado que creó la OT (supervisor, administrativo, etc.)
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
    # Normalización de patente (KG.JV93 -> KGJV93, etc.)
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

    # La solicitud sigue apuntando a un TALLER (andén específico)
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
        managed = False
        db_table = "solicitudes_ingreso_vehiculo"
        ordering = ["-creado_en"]
        verbose_name = "Solicitud de Ingreso de Vehículo"
        verbose_name_plural = "Solicitudes de Ingreso de Vehículos"

    def __str__(self):
        return f"{self.vehiculo.patente} - {self.fecha_solicitada} ({self.estado})"


class Pausa(models.Model):
    class Meta:
        managed = False
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
        return f"Pausa OT {self.ot.ot_id} - {self.ot.patente_id} ({estado})"


# ===========================================
# TABLA: INCIDENTES
# ===========================================
class Incidente(models.Model):
    class Meta:
        managed = False
        db_table = "incidentes"

    incidente_id = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(null=True, blank=True)
    descripcion = models.CharField(max_length=1000)

    vehiculo = models.ForeignKey(
        Vehiculo,
        db_column="patente",
        to_field="patente",
        on_delete=models.RESTRICT,
        related_name="incidentes",
    )
    empleado = models.ForeignKey(
        Empleado,
        db_column="rut",
        to_field="rut",
        on_delete=models.RESTRICT,
        related_name="incidentes",
    )

    def __str__(self):
        return f"Incidente #{self.incidente_id} - {self.vehiculo_id}"


# ===========================================
# TABLA: LLAVES
# ===========================================
class Llave(models.Model):
    class Meta:
        managed = False
        db_table = "llaves"

    llave_id = models.AutoField(primary_key=True)
    estado = models.CharField(max_length=50, default="Disponible")

    empleado = models.ForeignKey(
        Empleado,
        db_column="rut",
        to_field="rut",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,   # ON DELETE SET NULL
        related_name="llaves",
    )

    vehiculo = models.ForeignKey(
        Vehiculo,
        db_column="patente",
        to_field="patente",
        on_delete=models.RESTRICT,  # ON DELETE RESTRICT
        related_name="llaves",
    )

    def __str__(self):
        asignada = self.empleado.rut if self.empleado_id else "Sin asignar"
        return f"Llave #{self.llave_id} - {self.vehiculo_id} ({asignada})"


# ===========================================
# TABLA: DESIGNACION VEHICULAR
# ===========================================
class DesignacionVehicular(models.Model):
    class Meta:
        managed = False
        db_table = "designacion_vehicular"

    prestamo_id = models.AutoField(primary_key=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=50, default="En uso")

    vehiculo = models.ForeignKey(
        Vehiculo,
        db_column="patente",
        to_field="patente",
        on_delete=models.RESTRICT,
        related_name="designaciones",
    )

    empleado = models.ForeignKey(
        Empleado,
        db_column="empleados_rut",
        to_field="rut",
        on_delete=models.RESTRICT,
        related_name="designaciones_vehiculares",
    )

    def __str__(self):
        return f"Préstamo #{self.prestamo_id} - {self.vehiculo_id} -> {self.empleado_id}"


# ===========================================
# TABLA: REPUESTOS
# ===========================================
class Repuesto(models.Model):
    class Meta:
        managed = False
        db_table = "repuestos"

    repuesto_id = models.AutoField(primary_key=True)
    cantidad = models.IntegerField(default=1)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=500, null=True, blank=True)

    orden_trabajo = models.ForeignKey(
        "OrdenTrabajo",
        db_column="ot_id",
        on_delete=models.CASCADE,  # ON DELETE CASCADE
        related_name="repuestos",
    )

    def __str__(self):
        return f"{self.nombre} (x{self.cantidad}) - OT {self.orden_trabajo_id}"

# ===========================================
# TABLA: CONTROL DE ACCESO
# ===========================================
class ControlAcceso(models.Model):
    """
    Tabla control_acceso (ingreso/salida a recinto).
    """
    class Meta:
        managed = False
        db_table = "control_acceso"

    control_id = models.AutoField(primary_key=True)
    fecha_ingreso = models.DateField()
    fecha_salida = models.DateField(null=True, blank=True)

    guardia_ingreso = models.ForeignKey(
        Empleado,
        db_column="rut_guardia_ingreso",
        to_field="rut",
        on_delete=models.RESTRICT,
        related_name="controles_acceso_ingreso",
    )

    vehiculo = models.ForeignKey(
        Vehiculo,
        db_column="patente",
        to_field="patente",
        on_delete=models.RESTRICT,
        related_name="controles_acceso",
    )

    guardia_salida = models.ForeignKey(
        Empleado,
        db_column="rut_guardia_salida",
        to_field="rut",
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        related_name="controles_acceso_salida",
    )

    chofer = models.ForeignKey(
        Empleado,
        db_column="rut_chofer",
        to_field="rut",
        on_delete=models.RESTRICT,
        related_name="controles_acceso_chofer",
    )

    # 👇 NUEVOS CAMPOS PARA TRAZA DE OPERACIÓN FORZADA
    forzado = models.BooleanField(default=False)
    motivo_forzado = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Control #{self.control_id} - {self.vehiculo_id}"
