# autenticacion/views_pages.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout

from vehiculos.models import Vehiculo
from autenticacion.models import Empleado
from ordenestrabajo.models import OrdenTrabajo
from talleres.models import Taller

from autenticacion.roles import (
    chofer_only,
    chofer_or_supervisor,
    mecanico_only,
    mecanico_or_supervisor,
    supervisor_only,
    todos_roles,
)

# ==========================================================
# 🔐 LOGIN — Página pública
# ==========================================================
def login_page(request):
    if request.user.is_authenticated:
        return redirect("inicio")

    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("inicio")
        else:
            error = "Usuario o contraseña incorrectos"

    return render(request, "inicio-sesion.html", {"error": error})


# ==========================================================
# 🔓 LOGOUT
# ==========================================================
def logout_web(request):
    logout(request)
    return redirect("inicio-sesion")


# ==========================================================
# 🏠 DASHBOARD PRINCIPAL
# ==========================================================
@login_required(login_url='inicio-sesion')
def inicio_page(request):
    user = request.user

    empleado = (
        Empleado.objects
        .select_related('taller')
        .filter(usuario=user.username)
        .first()
    )

    total_vehiculos = Vehiculo.objects.count()
    en_taller = OrdenTrabajo.objects.filter(estado='En Taller').count()
    en_proceso = OrdenTrabajo.objects.filter(
        estado__in=['En Proceso', 'Pendiente']
    ).count()
    empleados_activos = Empleado.objects.filter(is_active=True).count()

    kpis = {
        'total_vehiculos': total_vehiculos,
        'en_taller': en_taller,
        'en_proceso': en_proceso,
        'empleados_activos': empleados_activos,
    }

    return render(request, 'inicio.html', {
        'empleado': empleado,
        'kpis': kpis,
        'menu_active': 'inicio',
    })


# ==========================================================
# 🚗 INGRESO DE VEHÍCULOS
# ==========================================================
@login_required(login_url='inicio-sesion')
@chofer_or_supervisor
def ingreso_vehiculos_page(request):

    user = request.user

    empleado = (
        Empleado.objects
        .select_related('taller')
        .filter(usuario=user.username)
        .first()
    )

    talleres = Taller.objects.all().order_by('nombre')
    vehiculos = Vehiculo.objects.all().order_by('patente')

    if request.method == "POST":
        patente = (request.POST.get("patente") or "").strip().upper()
        taller_id = request.POST.get("taller_id") or None
        descripcion = (request.POST.get("descripcion") or "").strip()

        if not patente:
            messages.error(request, "Debe seleccionar una patente.")
            return redirect("ingreso-vehiculos")

        if not taller_id:
            if empleado and empleado.taller_id:
                taller_id = empleado.taller_id
            else:
                messages.error(request, "Debe seleccionar un taller.")
                return redirect("ingreso-vehiculos")

        vehiculo = Vehiculo.objects.filter(patente=patente).first()
        taller = Taller.objects.filter(taller_id=taller_id).first()

        if not vehiculo or not taller:
            messages.error(request, "Datos inválidos.")
            return redirect("ingreso-vehiculos")

        ot_activa = OrdenTrabajo.objects.filter(
            patente=vehiculo,
            estado__in=["Pendiente", "En Proceso", "En Taller"],
        ).first()

        if ot_activa:
            messages.warning(
                request,
                f"Ya existe una OT activa #{ot_activa.ot_id} para {patente}."
            )
            return redirect("ingreso-vehiculos")

        ahora = timezone.now()

        OrdenTrabajo.objects.create(
            fecha_ingreso=ahora.date(),
            hora_ingreso=ahora.time().replace(microsecond=0),
            descripcion=descripcion,
            estado="En Taller",
            patente=vehiculo,
            taller=taller,
            rut=empleado,
            rut_creador=empleado,
        )

        vehiculo.estado = "En Taller"
        vehiculo.ubicacion = taller.nombre
        vehiculo.save()

        messages.success(
            request,
            f"Vehículo {patente} ingresado al taller {taller.nombre}."
        )

        return redirect("ingreso-vehiculos")

    return render(request, "ingreso-vehiculos.html", {
        "menu_active": "ingreso_vehiculos",
        "empleado": empleado,
        "talleres": talleres,
        "vehiculos": vehiculos,
    })


# ==========================================================
# 📄 FICHA VEHÍCULO — VERSIÓN DUPLICADA (SE DESHABILITA)
# ==========================================================
"""
@login_required(login_url='inicio-sesion')
@todos_roles
def ficha_vehiculo_page(request):
    # ⚠️ Esta versión queda obsoleta
    # La verdadera está en vehiculos/views.py → api_ficha + ficha_vehiculo
    patente = (request.GET.get("patente") or "").strip().upper()
    empleado = (
        Empleado.objects.select_related('taller')
        .filter(usuario=request.user.username).first()
    )
    return render(request, 'ficha-vehiculo.html', {
        "menu_active": "ficha_vehiculo",
        "empleado": empleado,
        "patente": patente,
    })
"""
# ==========================================================


# ==========================================================
# 🛠️ ASIGNACIÓN DE TALLER (Supervisor)
# ==========================================================
@login_required(login_url='inicio-sesion')
@supervisor_only
def asignacion_taller_page(request):
    supervisor = (
        Empleado.objects
        .select_related("taller")
        .filter(usuario=request.user.username)
        .first()
    )

    if not supervisor or not supervisor.taller:
        return render(request, "asignacion-taller.html", {
            "menu_active": "asignacion_taller",
            "supervisor": supervisor,
            "ots": [],
            "mecanicos": [],
            "error": "No se pudo determinar tu taller."
        })

    mecanicos = (
        Empleado.objects
        .filter(
            cargo="MECANICO",
            taller_id=supervisor.taller.taller_id
        )
        .order_by("nombre")
    )

    if request.method == "POST":
        ot_id = request.POST.get("ot_id")
        mecanico_rut = request.POST.get("mecanico_rut")
        comentario = (request.POST.get("comentario") or "").strip()

        if not comentario:
            return JsonResponse({"success": False, "message": "Debe ingresar comentario."})

        ot = (
            OrdenTrabajo.objects
            .filter(
                ot_id=ot_id,
                estado="Pendiente",
                taller_id=supervisor.taller.taller_id
            )
            .first()
        )

        if not ot:
            return JsonResponse({"success": False, "message": "OT inválida."})

        mecanico = (
            Empleado.objects
            .filter(
                rut=mecanico_rut,
                cargo="MECANICO",
                taller_id=supervisor.taller.taller_id
            )
            .first()
        )

        if not mecanico:
            return JsonResponse({"success": False, "message": "Mecánico inválido."})

        ot.estado = "En Taller"
        ot.rut = mecanico
        ot.descripcion = (ot.descripcion or "") + f"\n[Supervisor {supervisor.usuario}] {comentario}"
        ot.save()

        vehiculo = Vehiculo.objects.filter(patente=ot.patente_id).first()
        if vehiculo:
            vehiculo.estado = "En Taller"
            vehiculo.ubicacion = supervisor.taller.nombre
            vehiculo.save()

        return JsonResponse({"success": True})

    ots_pendientes = (
        OrdenTrabajo.objects
        .filter(
            estado="Pendiente",
            taller_id=supervisor.taller.taller_id
        )
        .select_related("patente")
        .order_by("-fecha_ingreso", "-hora_ingreso")
    )

    return render(request, "asignacion-taller.html", {
        "menu_active": "asignacion_taller",
        "supervisor": supervisor,
        "ots": ots_pendientes,
        "mecanicos": mecanicos,
    })
