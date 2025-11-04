# autenticacion/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class EmpleadoManager(BaseUserManager):
    def create_user(self, usuario, password=None, **extra_fields):
        if not usuario:
            raise ValueError("El campo 'usuario' es obligatorio")
        user = self.model(usuario=usuario.strip(), **extra_fields)
        user.set_password(password)
        user.full_clean()  # valida según las reglas del modelo
        user.save(using=self._db)
        return user

    def create_superuser(self, usuario, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('taller_id', 1)
        extra_fields.setdefault('rut', '00000000-0')
        extra_fields.setdefault('nombre', 'Administrador')
        extra_fields.setdefault('cargo', 'Administrador')

        if extra_fields.get('is_staff') is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self.create_user(usuario, password, **extra_fields)


class Empleado(AbstractBaseUser, PermissionsMixin):
    # 🔹 Opciones para región
    REGION_CHOICES = [
        ('Metropolitana', 'Región Metropolitana'),
        ('Valparaiso', 'Valparaíso'),
        ('Biobio', 'Biobío'),
        ('Araucania', 'La Araucanía'),
        ('Los Lagos', 'Los Lagos'),
        ('Otra', 'Otra región'),
    ]

    # 🔹 Opciones para horario
    HORARIO_CHOICES = [
        ('Diurno', 'Turno Diurno'),
        ('Nocturno', 'Turno Nocturno'),
        ('Mixto', 'Turno Mixto'),
    ]

    # 🔹 Opciones para cargo / rol
    CARGO_CHOICES = [
        ('Administrador', 'Administrador'),
        ('Chofer', 'Chofer'),
        ('Supervisor', 'Supervisor'),
        ('Mecanico/Administrativo', 'Mecánico/Administrativo'),
    ]

    rut = models.CharField(primary_key=True, max_length=12)
    nombre = models.CharField(max_length=100)
    cargo = models.CharField(max_length=50, choices=CARGO_CHOICES, default='Chofer')
    region = models.CharField(max_length=50, choices=REGION_CHOICES, null=True, blank=True)
    horario = models.CharField(max_length=100, choices=HORARIO_CHOICES, null=True, blank=True)
    disponibilidad = models.PositiveSmallIntegerField(default=1)
    usuario = models.CharField(max_length=45, unique=True)

    # 🧩 Relación con taller
    taller = models.ForeignKey(
        'talleres.Taller',
        db_column='taller_id',
        on_delete=models.DO_NOTHING,
        default=1
    )

    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    objects = EmpleadoManager()

    USERNAME_FIELD = 'usuario'
    REQUIRED_FIELDS = ['rut', 'nombre']

    class Meta:
        db_table = 'empleados'
        managed = False  # ⚠️ Django no crea ni migra esta tabla

    def save(self, *args, **kwargs):
        """Aplica valores por defecto y limpieza antes de guardar."""
        if not self.taller_id:
            self.taller_id = 1
        if self.disponibilidad is None:
            self.disponibilidad = 1
        if not self.region:
            self.region = "Otra"
        if not self.horario:
            self.horario = "Diurno"
        if not self.cargo:
            self.cargo = "Chofer"

        # Limpieza de texto
        self.nombre = self.nombre.strip().title()
        self.usuario = self.usuario.strip()
        self.rut = self.rut.strip()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.usuario})"
