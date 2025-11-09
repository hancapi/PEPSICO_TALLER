# vehiculos/models.py
from django.db import models

class Vehiculo(models.Model):
    class Meta:
        managed = False
        db_table = 'vehiculos'

    patente = models.CharField(primary_key=True, max_length=20)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.IntegerField(null=True, blank=True)
    tipo = models.CharField(max_length=50, null=True, blank=True)
    estado = models.CharField(max_length=50, default='Disponible')
    ubicacion = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.patente
