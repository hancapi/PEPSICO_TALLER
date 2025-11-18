# talleres/views_agenda.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from autenticacion.roles import supervisor_only
from autenticacion.models import Empleado

@login_required(login_url="/inicio-sesion/")
@supervisor_only
def agenda_page(request):
    """Página de agenda para supervisores"""
    user = request.user
    empleado = (
        Empleado.objects.select_related("taller")
        .filter(usuario=user.username)
        .first()
    )

    return render(request, "agenda.html", {
        "menu_active": "agenda",
        "empleado": empleado,
        "TALLER_ID": empleado.taller.taller_id if empleado and empleado.taller else None
    })
