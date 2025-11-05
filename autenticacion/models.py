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
        extra_fields.setdefault('cargo', 'ADMIN')
        extra_fields.setdefault('region', 'RM')
        extra_fields.setdefault('horario', 'ADMIN')
        extra_fields.setdefault('disponibilidad', True)
        extra_fields.setdefault('region', 'RM')  # Valor por defecto para superuser
        extra_fields.setdefault('horario', 'ADMIN')  # Valor por defecto para superuser
        extra_fields.setdefault('disponibilidad', True)  # Superuser siempre disponible

        if extra_fields.get('is_staff') is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self.create_user(usuario, password, **extra_fields)


class Empleado(AbstractBaseUser, PermissionsMixin):
    # Opciones de roles/cargos
    CARGO_CHOICES = [
        ('CHOFER', 'Chofer'),
        ('SUPERVISOR', 'Supervisor'),
        ('MECANICO', 'Mecánico/Administrativo'),
        ('ADMIN', 'Administrador'),
    ]
    
    # Opciones de regiones chilenas
    REGION_CHOICES = [
        ('AR', 'Arica y Parinacota'),
        ('TA', 'Tarapacá'),
        ('AN', 'Antofagasta'),
        ('AT', 'Atacama'),
        ('CO', 'Coquimbo'),
        ('VA', 'Valparaíso'),
        ('RM', 'Metropolitana'),
        ('LI', 'Libertador Bernardo O\'Higgins'),
        ('MA', 'Maule'),
        ('NB', 'Ñuble'),
        ('BI', 'Biobío'),
        ('AU', 'Araucanía'),  # ✅ Corregido: cambiado de 'AR' a 'AU'
        ('AR', 'Araucanía'),
        ('LR', 'Los Ríos'),
        ('LL', 'Los Lagos'),
        ('AI', 'Aysén'),
        ('MG', 'Magallanes'),
    ]
    
    # Opciones de horarios
    HORARIO_CHOICES = [
        ('DIURNO', 'Diurno (08:00 - 17:00)'),
        ('VESPERTINO', 'Vespertino (14:00 - 23:00)'),
        ('NOCTURNO', 'Nocturno (22:00 - 07:00)'),
        ('MIXTO', 'Mixto'),
        ('ADMIN', 'Administrativo (09:00 - 18:00)'),
        ('TURNO', 'Por turnos'),
    ]

    rut = models.CharField(primary_key=True, max_length=12)
    nombre = models.CharField(max_length=100)

    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES, default='CHOFER')
    region = models.CharField(max_length=50, choices=REGION_CHOICES, default='RM', null=True, blank=True)
    horario = models.CharField(max_length=100, choices=HORARIO_CHOICES, default='DIURNO', null=True, blank=True)
    disponibilidad = models.BooleanField(default=True, verbose_name='Disponible')
    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES)
    region = models.CharField(max_length=50, choices=REGION_CHOICES, default='RM')
    horario = models.CharField(max_length=100, choices=HORARIO_CHOICES, default='DIURNO')
    
    # Campo disponibilidad mejorado - usando BooleanField
    disponibilidad = models.BooleanField(default=True, verbose_name='Disponible')
    

    usuario = models.CharField(max_length=45, unique=True)

    taller = models.ForeignKey(
        'talleres.Taller',
        db_column='taller_id',
        on_delete=models.DO_NOTHING,
        default=1
    )

    password = models.CharField(max_length=128)
    
    # CORRECTO: last_login como DateTimeField (fecha y hora juntas)
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='Último acceso')
    
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    objects = EmpleadoManager()

    USERNAME_FIELD = 'usuario'
    REQUIRED_FIELDS = ['rut', 'nombre']

    class Meta:
        db_table = 'empleados'
        managed = False

    def save(self, *args, **kwargs):
        """
        Aplica valores por defecto y limpieza antes de guardar.
        """
        if not self.taller_id:
            self.taller_id = 1
            
        
        # Disponibilidad por defecto es True (disponible)
        if self.disponibilidad is None:
            self.disponibilidad = True
            
        if not self.region:
            self.region = "RM"
        if not self.horario:
            self.horario = "DIURNO"

        # Limpieza de datos
        self.nombre = self.nombre.strip().title()
        self.usuario = self.usuario.strip()
        self.rut = self.rut.strip()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.usuario})"

    @property
    def estado_disponibilidad(self):
        """Propiedad para obtener el estado como texto"""
        return "Disponible" if self.disponibilidad else "No disponible"

    @property
    def ultimo_acceso_formateado(self):
        """Devuelve last_login formateado como string legible"""
        if self.last_login:
            return self.last_login.strftime("%d/%m/%Y %H:%M")
        return "Nunca"

        return "Disponible" if self.disponibilidad else "No disponible"
