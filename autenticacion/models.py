# autenticacion/models.py
from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from talleres.models import Recinto  # usamos Recinto (FK recinto_id)


# ===========================================
# MODELO: Empleado (tabla existente en MySQL)
# ===========================================
class Empleado(models.Model):
    # ---- Choices: Cargos estándar ----
    CARGOS = [
        ('CHOFER', 'Chofer'),
        ('SUPERVISOR', 'Supervisor'),
        ('MECANICO', 'Mecánico'),
        ('ADMINISTRATIVO', 'Administrativo'),
        ('GUARDIA', 'Guardia'),      
    ]

    # ---- Choices: Regiones de Chile ----
    REGIONES_CHILE = [
        ('XV', 'Arica y Parinacota'),
        ('I', 'Tarapacá'),
        ('II', 'Antofagasta'),
        ('III', 'Atacama'),
        ('IV', 'Coquimbo'),
        ('V', 'Valparaíso'),
        ('RM', 'Región Metropolitana'),
        ('VI', 'O’Higgins'),
        ('VII', 'Maule'),
        ('XVI', 'Ñuble'),
        ('VIII', 'Biobío'),
        ('IX', 'La Araucanía'),
        ('XIV', 'Los Ríos'),
        ('X', 'Los Lagos'),
        ('XI', 'Aysén'),
        ('XII', 'Magallanes'),
    ]

    # ---- Choices: Horarios típicos ----
    HORARIOS = [
        ('07:00-16:00', '07:00 a 16:00'),
        ('08:00-17:00', '08:00 a 17:00'),
        ('09:00-18:00', '09:00 a 18:00'),
        ('10:00-19:00', '10:00 a 19:00'),
    ]

    class Meta:
        managed = False
        db_table = 'empleados'

    rut = models.CharField(primary_key=True, max_length=12)
    nombre = models.CharField(max_length=100)

    # En BD: cargo VARCHAR(50)
    cargo = models.CharField(
        max_length=50,
        choices=CARGOS,
    )

    # En BD: region VARCHAR(50)
    region = models.CharField(
        max_length=50,
        choices=REGIONES_CHILE,
        null=True,
        blank=True,
    )

    # En BD: horario VARCHAR(100)
    horario = models.CharField(
        max_length=100,
        choices=HORARIOS,
        default='08:00-17:00',
    )

    disponibilidad = models.BooleanField(default=True)
    password = models.CharField(max_length=128)
    usuario = models.CharField(max_length=45, unique=True)

    # 🔹 Empleado pertenece a un RECINTO (FK recinto_id)
    recinto = models.ForeignKey(
        Recinto,
        on_delete=models.RESTRICT,
        db_column='recinto_id',
        related_name='empleados',
    )

    last_login = models.DateTimeField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.usuario} ({self.rut})"

    # Vinculación lógica al objeto User de Django
    @property
    def linked_user(self):
        """Devuelve el objeto User vinculado por 'usuario', si existe."""
        try:
            return User.objects.get(username=self.usuario)
        except User.DoesNotExist:
            return None

    @property
    def email(self) -> str:
        """
        Email lógico basado en el usuario de dominio.
        Se definió que el origen real de correo es usuario + '@pepsico.cl'.
        """
        return f"{self.usuario}@pepsico.cl"


# ===========================================
# SINCRONIZACIÓN AUTOMÁTICA DE GRUPOS
# ===========================================
@receiver(post_save, sender=Empleado)
def sync_user_group(sender, instance: Empleado, **kwargs):
    """
    Sincroniza automáticamente el grupo del usuario Django según el cargo.
    Usa el campo `usuario` para enlazar, sin modificar la tabla MySQL.
    """
    user = instance.linked_user
    if not user:
        return  # no hay usuario Django vinculado

    group_name = instance.cargo.upper().strip()
    group, _ = Group.objects.get_or_create(name=group_name)

    # limpiar grupos previos y asignar el correcto
    user.groups.clear()
    user.groups.add(group)

    # si es supervisor, lo marcamos como staff
    user.is_staff = (group_name == 'SUPERVISOR')
    user.save()
