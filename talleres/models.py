# talleres/models.py
from django.db import models

class Taller(models.Model):
    class Meta:
        managed = False
        db_table = 'talleres'

    taller_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=100)
    encargado_taller = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre
