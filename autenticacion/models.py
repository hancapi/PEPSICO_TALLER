# autenticacion/models.py
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


class Empleado(models.Model):
    class Meta:
        managed = False
        db_table = 'empleados'

    rut = models.CharField(primary_key=True, max_length=12)
    nombre = models.CharField(max_length=100)
    cargo = models.CharField(max_length=50)
    region = models.CharField(max_length=50, null=True, blank=True)
    horario = models.CharField(max_length=100, null=True, blank=True)
    disponibilidad = models.BooleanField()
    password = models.CharField(max_length=128)  # hash de Django
    usuario = models.CharField(max_length=45, unique=True)
    taller = models.ForeignKey(Taller, on_delete=models.RESTRICT, db_column='taller_id')
    last_login = models.DateTimeField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.usuario} ({self.rut})"
