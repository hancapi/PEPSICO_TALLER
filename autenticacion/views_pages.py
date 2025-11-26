# autenticacion/views_pages.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q

from vehiculos.models import Vehiculo
from vehiculos.forms import VehiculoForm  # ModelForm oficial de Vehiculo
from autenticacion.forms import EmpleadoForm
from autenticacion.models import Empleado
from ordenestrabajo.models import (
    OrdenTrabajo,
    SolicitudIngresoVehiculo,
    DesignacionVehicular,
    ControlAcceso,
)
from talleres.models import Taller, Recinto          # 👈 agrega Recinto aquí
from talleres.forms import RecintoForm, TallerForm  # 👈 NUEVO

from autenticacion.roles import (
    chofer_only,
    chofer_or_supervisor,
    mecanico_only,
    mecanico_or_supervisor,
    supervisor_only,
    todos_roles,
    guardia_only,
    admin_web_only,
)

# Vista canónica del guardia
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
@login_required(login_url="inicio-sesion")
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
# ==========================================================
@login_required(login_url="inicio-sesion")
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
        SolicitudIngresoVehiculo.objects.create(
            vehiculo=vehiculo,
            chofer=empleado,
            taller=taller,
            fecha_solicitada=ahora.date(),
            estado="PENDIENTE",
            # descripcion=descripcion,  # si tu modelo lo tiene
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
@login_required(login_url="inicio-sesion")
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
# 🚧 CONTROL DE ACCESO (GUARDIA)
# ==========================================================
@login_required(login_url="inicio-sesion")
@guardia_only
def control_acceso_page(request):
    return control_acceso_guardia(request)


# ==========================================================
# 🧩 ADMIN WEB — Panel principal
# ==========================================================
@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_panel_page(request):
    return render(request, "admin_panel.html", {
        "menu_active": "admin-web"
    })


# ==========================================================
# 🧩 ADMIN WEB — VEHÍCULOS (Listado)
# ==========================================================
@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_vehiculos_page(request):
    q_patente = (request.GET.get("patente") or "").strip().upper()
    q_marca   = (request.GET.get("marca") or "").strip()
    q_modelo  = (request.GET.get("modelo") or "").strip()
    q_estado  = (request.GET.get("estado") or "").strip()

    qs = Vehiculo.objects.all().order_by("patente")

    if q_patente:
        qs = qs.filter(patente__icontains=q_patente)
    if q_marca:
        qs = qs.filter(marca__icontains=q_marca)
    if q_modelo:
        qs = qs.filter(modelo__icontains=q_modelo)
    if q_estado:
        qs = qs.filter(estado=q_estado)

    estados = (
        Vehiculo.objects.exclude(estado__isnull=True)
        .values_list("estado", flat=True)
        .distinct()
        .order_by("estado")
    )

    context = {
        "menu_active": "admin-web",
        "vehiculos": qs,
        "f_patente": q_patente,
        "f_marca": q_marca,
        "f_modelo": q_modelo,
        "f_estado": q_estado,
        "estados": estados,
    }
    return render(request, "admin_vehiculos.html", context)


# ==========================================================
# 🧩 ADMIN WEB — VEHÍCULOS (Nuevo)
# ==========================================================
@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_vehiculo_create(request):
    if request.method == "POST":
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehículo creado correctamente.")
            return redirect("autenticacion:admin-web-vehiculos")
    else:
        form = VehiculoForm()

    return render(request, "admin_vehiculo_form.html", {
        "menu_active": "admin-web",
        "form": form,
        "is_edit": False,
    })


# ==========================================================
# 🧩 ADMIN WEB — VEHÍCULOS (Editar)
# ==========================================================
@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_vehiculo_edit(request, patente):
    vehiculo = get_object_or_404(Vehiculo, patente=patente)

    if request.method == "POST":
        form = VehiculoForm(request.POST, instance=vehiculo)
        form.fields["patente"].disabled = True
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Vehículo {vehiculo.patente} actualizado correctamente."
            )
            return redirect("autenticacion:admin-web-vehiculos")
    else:
        form = VehiculoForm(instance=vehiculo)
        form.fields["patente"].disabled = True

    return render(request, "admin_vehiculo_form.html", {
        "menu_active": "admin-web",
        "form": form,
        "is_edit": True,
        "vehiculo": vehiculo,
    })


# ==========================================================
# 🧩 ADMIN WEB — VEHÍCULOS (Eliminar)
# ==========================================================
@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_vehiculo_delete(request, patente):
    vehiculo = get_object_or_404(Vehiculo, patente=patente)

    if request.method == "POST":
        patente_txt = vehiculo.patente
        vehiculo.delete()
        messages.success(
            request,
            f"Vehículo {patente_txt} eliminado correctamente."
        )
        return redirect("autenticacion:admin-web-vehiculos")

    return render(request, "admin_vehiculo_confirm_delete.html", {
        "menu_active": "admin-web",
        "vehiculo": vehiculo,
    })


# ==========================================================
# ⚙️ ADMIN WEB – EMPLEADOS (Listado)
# ==========================================================
@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_empleados_page(request):
    q_rut    = (request.GET.get("rut") or "").strip()
    q_nombre = (request.GET.get("nombre") or "").strip()
    q_cargo  = (request.GET.get("cargo") or "").strip()
    q_region = (request.GET.get("region") or "").strip()

    qs = (
        Empleado.objects
        .select_related("recinto")
        .all()
        .order_by("nombre")
    )

    if q_rut:
        qs = qs.filter(rut__icontains=q_rut)
    if q_nombre:
        qs = qs.filter(nombre__icontains=q_nombre)
    if q_cargo:
        qs = qs.filter(cargo=q_cargo)
    if q_region:
        qs = qs.filter(region=q_region)

    cargos = [c[0] for c in Empleado.CARGOS]
    regiones = [r[0] for r in Empleado.REGIONES_CHILE]

    return render(request, "admin_empleados.html", {
        "menu_active": "admin-web",
        "empleados": qs,
        "f_rut": q_rut,
        "f_nombre": q_nombre,
        "f_cargo": q_cargo,
        "f_region": q_region,
        "cargos": cargos,
        "regiones": regiones,
    })


# ==========================================================
# ⚙️ ADMIN WEB – EMPLEADOS (Nuevo)
# ==========================================================
@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_empleado_create(request):
    if request.method == "POST":
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Empleado creado correctamente.")
            return redirect("autenticacion:admin-web-empleados")
    else:
        form = EmpleadoForm()

    return render(request, "admin_empleado_form.html", {
        "menu_active": "admin-web",
        "form": form,
        "is_edit": False,
    })


# ==========================================================
# ⚙️ ADMIN WEB – EMPLEADOS (Editar)
# ==========================================================
@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_empleado_edit(request, rut):
    empleado = get_object_or_404(Empleado, rut=rut)

    if request.method == "POST":
        form = EmpleadoForm(request.POST, instance=empleado)
        # no permitimos cambiar rut desde la vista
        form.fields["rut"].disabled = True

        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Empleado {empleado.nombre} actualizado correctamente."
            )
            return redirect("autenticacion:admin-web-empleados")
    else:
        form = EmpleadoForm(instance=empleado)
        form.fields["rut"].disabled = True

    return render(request, "admin_empleado_form.html", {
        "menu_active": "admin-web",
        "form": form,
        "is_edit": True,
        "empleado": empleado,
    })


# ==========================================================
# ⚙️ ADMIN WEB – EMPLEADOS (Eliminar)
# ==========================================================
@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_empleado_delete(request, rut):
    empleado = get_object_or_404(Empleado, rut=rut)

    if request.method == "POST":
        nombre = empleado.nombre
        empleado.delete()
        messages.success(
            request,
            f"Empleado {nombre} eliminado correctamente."
        )
        return redirect("autenticacion:admin-web-empleados")

    return render(request, "admin_empleado_confirm_delete.html", {
        "menu_active": "admin-web",
        "empleado": empleado,
    })

# ==========================================================
# ⚙️ ADMIN WEB – Recintos (CRUD)
# ==========================================================
@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_recintos_page(request):
    recintos = Recinto.objects.all().order_by("nombre") if hasattr(Recinto, "nombre") else Recinto.objects.all().order_by("pk")
    return render(request, "admin_recintos.html", {
        "menu_active": "admin-web",
        "recintos": recintos,
    })


@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_recinto_create(request):
    if request.method == "POST":
        form = RecintoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Recinto creado correctamente.")
            return redirect("autenticacion:admin-web-recintos")
    else:
        form = RecintoForm()

    return render(request, "admin_recinto_form.html", {
        "menu_active": "admin-web",
        "form": form,
        "is_edit": False,
    })


@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_recinto_edit(request, pk):
    recinto = get_object_or_404(Recinto, pk=pk)

    if request.method == "POST":
        form = RecintoForm(request.POST, instance=recinto)
        if form.is_valid():
            form.save()
            messages.success(request, "Recinto actualizado correctamente.")
            return redirect("autenticacion:admin-web-recintos")
    else:
        form = RecintoForm(instance=recinto)

    return render(request, "admin_recinto_form.html", {
        "menu_active": "admin-web",
        "form": form,
        "is_edit": True,
        "recinto": recinto,
    })


@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_recinto_delete(request, pk):
    recinto = get_object_or_404(Recinto, pk=pk)

    if request.method == "POST":
        nombre = str(recinto)
        recinto.delete()
        messages.success(request, f"Recinto {nombre} eliminado correctamente.")
        return redirect("autenticacion:admin-web-recintos")

    return render(request, "admin_recinto_confirm_delete.html", {
        "menu_active": "admin-web",
        "recinto": recinto,
    })


# ==========================================================
# ⚙️ ADMIN WEB – Talleres (CRUD)
# ==========================================================
@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_talleres_page(request):
    talleres = (
        Taller.objects.select_related("recinto")
        .all()
        .order_by("recinto__nombre", "pk")
    )
    return render(request, "admin_talleres.html", {
        "menu_active": "admin-web",
        "talleres": talleres,
    })


@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_taller_create(request):
    if request.method == "POST":
        form = TallerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Taller creado correctamente.")
            return redirect("autenticacion:admin-web-talleres")
    else:
        form = TallerForm()

    return render(request, "admin_taller_form.html", {
        "menu_active": "admin-web",
        "form": form,
        "is_edit": False,
    })


@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_taller_edit(request, pk):
    taller = get_object_or_404(Taller, pk=pk)

    if request.method == "POST":
        form = TallerForm(request.POST, instance=taller)
        if form.is_valid():
            form.save()
            messages.success(request, "Taller actualizado correctamente.")
            return redirect("autenticacion:admin-web-talleres")
    else:
        form = TallerForm(instance=taller)

    return render(request, "admin_taller_form.html", {
        "menu_active": "admin-web",
        "form": form,
        "is_edit": True,
        "taller": taller,
    })


@login_required(login_url="inicio-sesion")
@admin_web_only
def admin_web_taller_delete(request, pk):
    taller = get_object_or_404(Taller, pk=pk)

    if request.method == "POST":
        nombre = str(taller)
        taller.delete()
        messages.success(request, f"Taller {nombre} eliminado correctamente.")
        return redirect("autenticacion:admin-web-talleres")

    return render(request, "admin_taller_confirm_delete.html", {
        "menu_active": "admin-web",
        "taller": taller,
    })