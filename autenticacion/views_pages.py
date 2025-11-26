# autenticacion/views_pages.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q

from vehiculos.models import Vehiculo
from autenticacion.models import Empleado
from ordenestrabajo.models import (
    OrdenTrabajo,
    SolicitudIngresoVehiculo,
    DesignacionVehicular,
    ControlAcceso,
)
from talleres.models import Taller

from autenticacion.roles import (
    chofer_only,
    chofer_or_supervisor,
    mecanico_only,
    mecanico_or_supervisor,
    supervisor_only,
    todos_roles,
    guardia_only,
    # guardia_or_supervisor  # lo puedes usar después si quieres
)

# ✅ Importamos la vista canónica del guardia
from ordenestrabajo.views_control_acceso import control_acceso_guardia


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
        .select_related('recinto')
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
# 🚗 SOLICITUD DE INGRESO DE VEHÍCULOS
#    (Chofer / Supervisor -> crea SolicitudIngresoVehiculo PENDIENTE)
# ==========================================================
@login_required(login_url='inicio-sesion')
@chofer_or_supervisor
def ingreso_vehiculos_page(request):

    user = request.user

    empleado = (
        Empleado.objects
        .select_related('recinto')
        .filter(usuario=user.username)
        .first()
    )

    # Lista de talleres: dejamos 1 por recinto (evitar duplicados "Santa rosa")
    qs_talleres = (
        Taller.objects
        .select_related('recinto')
        .order_by('recinto__nombre', 'nro_anden')
    )

    talleres = []
    vistos_recintos = set()
    for t in qs_talleres:
        rid = t.recinto_id
        if rid in vistos_recintos:
            continue
        vistos_recintos.add(rid)
        talleres.append(t)

    vehiculos = Vehiculo.objects.all().order_by('patente')

    if request.method == "POST":
        patente = (request.POST.get("patente") or "").strip().upper()
        taller_id = request.POST.get("taller_id") or None
        descripcion = (request.POST.get("descripcion") or "").strip()

        if not patente:
            messages.error(request, "Debe seleccionar una patente.")
            return redirect("ingreso-vehiculos")

        if not taller_id:
            messages.error(request, "Debe seleccionar un taller.")
            return redirect("ingreso-vehiculos")

        vehiculo = Vehiculo.objects.filter(patente=patente).first()
        taller = (
            Taller.objects
            .select_related('recinto')
            .filter(taller_id=taller_id)
            .first()
        )

        if not vehiculo or not taller:
            messages.error(request, "Datos inválidos.")
            return redirect("ingreso-vehiculos")

        # 🔎 Verificar si ya existe una OT activa
        ot_activa = OrdenTrabajo.objects.filter(
            patente=vehiculo,
            estado__in=["Pendiente", "En Proceso", "En Taller", "Pausado"],
        ).first()

        if ot_activa:
            messages.warning(
                request,
                f"Ya existe una OT activa #{ot_activa.ot_id} para {patente}."
            )
            return redirect("ingreso-vehiculos")

        # 🔎 Verificar si ya existe una solicitud pendiente para ese vehículo
        sol_pendiente = SolicitudIngresoVehiculo.objects.filter(
            vehiculo=vehiculo,
            estado="PENDIENTE",
        ).first()

        if sol_pendiente:
            messages.warning(
                request,
                f"Ya existe una solicitud de ingreso pendiente para el vehículo {patente}."
            )
            return redirect("ingreso-vehiculos")

        ahora = timezone.now()

        # ✅ NUEVO FLUJO:
        # Creamos una SolicitudIngresoVehiculo en estado PENDIENTE
        solicitud = SolicitudIngresoVehiculo.objects.create(
            vehiculo=vehiculo,
            chofer=empleado,          # quien está solicitando
            taller=taller,
            fecha_solicitada=ahora.date(),
            estado="PENDIENTE",
            # ⚠️ Si tu modelo tiene campo 'descripcion' / 'motivo',
            #     puedes mapear 'descripcion' del formulario aquí.
            # p.ej: descripcion=descripcion,
        )

        messages.success(
            request,
            f"Solicitud de ingreso creada para el vehículo {patente} en el taller "
            f"{taller.recinto.nombre}. Queda pendiente de asignación por el supervisor."
        )

        return redirect("ingreso-vehiculos")

    return render(request, "ingreso-vehiculos.html", {
        "menu_active": "ingreso_vehiculos",
        "empleado": empleado,
        "talleres": talleres,
        "vehiculos": vehiculos,
    })


# ==========================================================
# 🛠️ ASIGNACIÓN DE TALLER (Supervisor)
# ==========================================================
@login_required(login_url='inicio-sesion')
@supervisor_only
def asignacion_taller_page(request):
    supervisor = (
        Empleado.objects
        .select_related("recinto")
        .filter(usuario=request.user.username)
        .first()
    )

    if not supervisor or not supervisor.recinto:
        return render(request, "asignacion-taller.html", {
            "menu_active": "asignacion_taller",
            "supervisor": supervisor,
            "solicitudes": [],
            "mecanicos": [],
            "error": "No se pudo determinar tu taller (recinto)."
        })

    mecanicos = (
        Empleado.objects
        .filter(
            cargo="MECANICO",
            recinto=supervisor.recinto,
            is_active=True,
        )
        .order_by("nombre")
    )

    solicitudes = (
        SolicitudIngresoVehiculo.objects
        .select_related("vehiculo", "chofer", "taller")
        .filter(
            taller__recinto=supervisor.recinto,
            estado="PENDIENTE",
        )
        .order_by("fecha_solicitada", "creado_en")
    )

    return render(request, "asignacion-taller.html", {
        "menu_active": "asignacion_taller",
        "supervisor": supervisor,
        "solicitudes": solicitudes,
        "mecanicos": mecanicos,
    })


# ==========================================================
# 🚧 CONTROL DE ACCESO (GUARDIA DE RECINTO)
#    Wrapper hacia la vista canónica en ordenestrabajo
# ==========================================================
@login_required(login_url='inicio-sesion')
@guardia_only
def control_acceso_page(request):
    """
    Wrapper para reutilizar la lógica centralizada de control de acceso
    definida en ordenestrabajo.views_control_acceso.control_acceso_guardia,
    manteniendo el nombre de vista y las restricciones de rol (guardia_only).
    """
    return control_acceso_guardia(request)
