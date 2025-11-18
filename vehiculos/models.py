# vehiculos/models.py
from django.db import models

# ==========================================================
# Opciones (CHOICES) corporativas PepsiCo
# ==========================================================
TIPO_CHOICES = [
    ("Camión", "Camión"),
    ("Furgón", "Furgón"),
    ("Pickup", "Pickup"),
    ("Auto", "Auto"),
    ("Bus", "Bus"),
]

ESTADO_CHOICES = [
    ("Disponible", "Disponible"),
    ("En Taller", "En Taller"),
    ("En Proceso", "En Proceso"),
    ("Pendiente", "Pendiente"),
    ("Fuera de Servicio", "Fuera de Servicio"),
]

UBICACION_CHOICES = [
    ("Santiago", "Santiago"),
    ("Renca", "Renca"),
    ("Maipú", "Maipú"),
    ("Quilicura", "Quilicura"),
    ("Concepción", "Concepción"),
]


# ==========================================================
# Modelo Vehículo
# ==========================================================
class Vehiculo(models.Model):

    # 🔥 ESTA LÍNEA FALTABA 🔥
    ESTADO_CHOICES = ESTADO_CHOICES

    class Meta:
        managed = False                # Django NO maneja esta tabla
        db_table = 'vehiculos'         # Nombre real de la tabla

    patente = models.CharField(max_length=20, primary_key=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.IntegerField(null=True, blank=True)

    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        default="Camión",
        blank=True,
        null=True
    )

    estado = models.CharField(
        max_length=50,
        choices=ESTADO_CHOICES,
        default="Disponible"
    )

    ubicacion = models.CharField(
        max_length=100,
        choices=UBICACION_CHOICES,
        default="Santiago",
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):
        if self.patente:
            self.patente = (
                self.patente.replace(".", "")
                             .replace("-", "")
                             .strip()
                             .upper()
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patente} — {self.marca} {self.modelo}"
