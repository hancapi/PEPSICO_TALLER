# autenticacion/models.py
from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from talleres.models import Recinto  # usamos Recinto (FK recinto_id)

# Grupos base asociados a cargos operativos
BASE_ROLE_GROUPS = ['CHOFER', 'SUPERVISOR', 'MECANICO', 'ADMINISTRATIVO', 'GUARDIA']


# ===========================================
# MODELO: Empleado (tabla existente en MySQL)
# ===========================================
class Empleado(models.Model):
    # ---- Choices: Cargos estándar (SIN ADMIN_WEB) ----
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

    cargo = models.CharField(
        max_length=50,
        choices=CARGOS,
    )

    region = models.CharField(
        max_length=50,
        choices=REGIONES_CHILE,
        null=True,
        blank=True,
    )

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
        """
        return f"{self.usuario}@pepsico.cl"

    @property
    def is_admin_web(self) -> bool:
        """
        Devuelve True si el User asociado pertenece al grupo ADMIN_WEB.
        Esto es lo que usas en el template: e.is_admin_web
        """
        user = self.linked_user
        if not user:
            return False
        return user.groups.filter(name='ADMIN_WEB').exists()


# ===========================================
# SINCRONIZACIÓN AUTOMÁTICA DE GRUPOS
# ===========================================
@receiver(post_save, sender=Empleado)
def sync_user_group(sender, instance: Empleado, **kwargs):
    """
    Sincroniza automáticamente el grupo del usuario Django según el cargo.
    - Usa el campo `usuario` para enlazar, sin modificar la tabla MySQL.
    - NO toca el grupo ADMIN_WEB (eso lo maneja el formulario con un flag).
    """
    user = instance.linked_user
    if not user:
        return  # no hay usuario Django vinculado

    group_name = (instance.cargo or '').upper().strip()
    if not group_name:
        return

    # grupo asociado al cargo
    role_group, _ = Group.objects.get_or_create(name=group_name)

    # quitar solo grupos base (no tocamos ADMIN_WEB ni otros custom)
    base_groups = Group.objects.filter(name__in=BASE_ROLE_GROUPS)
    user.groups.remove(*base_groups)

    # agregar grupo del cargo
    user.groups.add(role_group)

    # staff si es SUPERVISOR o si además tiene ADMIN_WEB
    has_admin_web = user.groups.filter(name='ADMIN_WEB').exists()
    is_supervisor = (group_name == 'SUPERVISOR')
    user.is_staff = is_supervisor or has_admin_web
    user.save()
