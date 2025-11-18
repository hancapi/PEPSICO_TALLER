# documentos/models.py
from django.db import models
from ordenestrabajo.models import OrdenTrabajo
from vehiculos.models import Vehiculo


def upload_to_vehiculo(instance, filename):
    # documentos para vehículo sueltos
    return f"vehiculos/{instance.patente_id}/{filename}"


def upload_to_ot(instance, filename):
    # documentos ligados a OT específica
    return f"ordenes/{instance.ot_id}/{filename}"


class Documento(models.Model):

    TIPO_CHOICES = (
        ('FOTO', 'Fotografía'),
        ('INFORME', 'Informe'),
        ('OTRO', 'Otro'),
    )

    # FK OT (normal)
    ot = models.ForeignKey(
        OrdenTrabajo,
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='documentos'
    )

    # FK a Vehiculo PERO sin constraint físico (como en tu migración existente)
    patente = models.ForeignKey(
        Vehiculo,
        to_field='patente',
        db_column='patente',
        on_delete=models.RESTRICT,
        null=True, blank=True,
        related_name='documentos',
        db_constraint=False,
        db_index=True,
    )

    tipo = models.CharField(max_length=12, choices=TIPO_CHOICES, default='OTRO')
    titulo = models.CharField(max_length=200)
    archivo = models.FileField(upload_to=upload_to_ot)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documentos'
        ordering = ['-creado_en']
        managed = False   

    def save(self, *args, **kwargs):

        # Si no tiene OT pero sí patente → va a carpeta de vehículo
        if self.ot is None and self.patente_id is not None:
            self.archivo.field.upload_to = upload_to_vehiculo

        super().save(*args, **kwargs)

    def __str__(self):
        ref = f"OT {self.ot_id}" if self.ot_id else f"Veh {self.patente_id}"
        return f"{self.titulo} ({ref})"
