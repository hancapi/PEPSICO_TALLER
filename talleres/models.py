# talleres/models.py
from django.db import models

# Opciones de ubicación estándar (mismas que en vehiculos.models)
UBICACION_CHOICES = [
    ("Santiago", "Santiago"),
    ("Renca", "Renca"),
    ("Maipú", "Maipú"),
    ("Quilicura", "Quilicura"),
    ("Concepción", "Concepción"),
]


class Recinto(models.Model):
    """
    Mapea la tabla base RECINTO.

    Campos en BD:
      - recinto_id INT PK AUTO_INCREMENT
      - nombre VARCHAR(100)
      - ubicacion VARCHAR(100)
      - jefe_recinto VARCHAR(255)
    """
    recinto_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)

    # Ahora es un select en el admin gracias a choices
    ubicacion = models.CharField(
        max_length=100,
        choices=UBICACION_CHOICES,
        default="Santiago",
    )

    jefe_recinto = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "recinto"

    def __str__(self):
        return self.nombre


class Taller(models.Model):
    """
    Mapea la tabla TALLERES, asociado a un RECINTO.

    Campos en BD:
      - taller_id INT PK AUTO_INCREMENT
      - nro_anden INT(2) NOT NULL UNIQUE
      - encargado_taller VARCHAR(255) NOT NULL
      - recinto_id INT FK -> recinto(recinto_id)
    """
    taller_id = models.AutoField(primary_key=True)

    # 👉 Nro andén ahora se autogenera y NO es editable desde el admin
    nro_anden = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        editable=False,   # no aparece en formularios
    )

    encargado_taller = models.CharField(max_length=255)

    recinto = models.ForeignKey(
        Recinto,
        models.DO_NOTHING,
        db_column="recinto_id",
        related_name="talleres",
    )

    class Meta:
        managed = False
        db_table = "talleres"
        # La UNIQUE de nro_anden está definida en MySQL (uq_taller_nro_anden).

    def __str__(self):
        # Representación legible combinando recinto + andén
        return f"Andén {self.nro_anden} — {self.recinto.nombre}"

    # ===== Compatibilidad hacia atrás =====
    @property
    def nombre(self):
        """Compatibilidad con código antiguo que hacía: taller.nombre"""
        return f"Andén {self.nro_anden}"

    @property
    def ubicacion(self):
        """Compatibilidad con código antiguo: taller.ubicacion"""
        return self.recinto.ubicacion

    # ===== Autogenerar nro_anden de forma incremental =====
    def save(self, *args, **kwargs):
        """
        Si nro_anden viene vacío, se asigna automáticamente:
        max(nro_anden) + 1.

        Esto mantiene la UNIQUE de BD y evita que el usuario
        tenga que escribir el número de andén a mano.
        """
        if self.nro_anden is None:
            last = Taller.objects.order_by('-nro_anden').first()
            last_val = last.nro_anden if last and last.nro_anden is not None else 0
            self.nro_anden = last_val + 1

        super().save(*args, **kwargs)
