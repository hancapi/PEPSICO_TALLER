# autenticacion/backends.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from autenticacion.models import Empleado


class EmpleadosBackend(BaseBackend):
    """
    Autentica contra la tabla 'empleados' y crea/actualiza un usuario 'sombra'
    en auth_user para poder usar sesiones/permisos/admin sin reemplazar AUTH_USER_MODEL.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        try:
            emp = Empleado.objects.get(usuario=username, is_active=True)
        except Empleado.DoesNotExist:
            return None

        # Promoción a hash en primer login si aún estuviera en texto plano (MVP)
        if len(emp.password) < 50 or emp.password.count('$') < 2:
            # Asumimos que el valor actual es texto plano
            if password == emp.password:
                emp.password = make_password(password)
                emp.save(update_fields=['password'])
            else:
                return None

        # Validación de contraseña hasheada
        if not check_password(password, emp.password):
            return None

        # Usuario "sombra" en auth_user
        expected_email = emp.email  # usuario + "@pepsico.cl"

        dj_user, created = User.objects.get_or_create(
            username=emp.usuario,
            defaults={
                'is_staff': emp.is_staff,
                'is_superuser': emp.is_superuser,
                'is_active': emp.is_active,
                'email': expected_email,
            }
        )

        # Sincroniza flags y email
        changed = False
        for f in ('is_staff', 'is_superuser', 'is_active'):
            if getattr(dj_user, f) != getattr(emp, f):
                setattr(dj_user, f, getattr(emp, f))
                changed = True

        if dj_user.email != expected_email:
            dj_user.email = expected_email
            changed = True

        if changed:
            dj_user.save()

        # Actualiza last_login en Empleado (dispara señal y sincroniza grupos)
        emp.last_login = timezone.now()
        emp.save(update_fields=['last_login'])

        return dj_user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return AnonymousUser()
