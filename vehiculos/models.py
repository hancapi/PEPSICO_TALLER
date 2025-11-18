# vehiculos/models.py
from django.db import models

# ==========================================================
# Opciones corporativas PepsiCo — NORMALIZADAS
# ==========================================================
TIPO_CHOICES = [
    ("Camión", "Camión"),
    ("Furgón", "Furgón"),
    ("Pickup", "Pickup"),
    ("Auto", "Auto"),
    ("Bus", "Bus"),
]

# Estados reales usados por la plataforma
ESTADO_VEHICULO_CHOICES = [
    ("Disponible", "Disponible"),
    ("En Taller", "En Taller"),
    ("En Proceso", "En Proceso"),
    ("Pausado", "Pausado"),
    ("Fuera de Servicio", "Fuera de Servicio"),
]

UBICACION_CHOICES = [
    ("Santiago", "Santiago"),
    ("Renca", "Renca"),
    ("Maipú", "Maipú"),
    ("Quilicura", "Quilicura"),
    ("Concepción", "Concepción"),
]


class Vehiculo(models.Model):

    class Meta:
        managed = False
        db_table = 'vehiculos'

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
        choices=ESTADO_VEHICULO_CHOICES,
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
