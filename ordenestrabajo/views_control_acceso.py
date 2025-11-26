# ordenestrabajo/views_control_acceso.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from autenticacion.models import Empleado
from vehiculos.models import Vehiculo
from .models import (
    ControlAcceso,
    DesignacionVehicular,
    OrdenTrabajo,
    SolicitudIngresoVehiculo,
)

# Estados de OT que permiten salida SIN forzar
ESTADOS_LIBERACION_OT = ["Finalizado", "No Reparable", "Sin Repuestos"]
# Estados que consideramos que el vehículo está libre/fuera del recinto
ESTADO_VEHICULO_FUERA = "Disponible"
# Estado que usaremos cuando el vehículo está DENTRO del recinto (pero aún no en taller)
ESTADO_VEHICULO_DENTRO = "En Recinto"


def _empleado_desde_user(user):
    try:
        return Empleado.objects.select_related("recinto").get(usuario=user.username)
    except Empleado.DoesNotExist:
        return None


def _normalizar_patente(p):
    if not p:
        return ""
    return (
        p.replace(".", "")
         .replace("-", "")
         .strip()
         .upper()
    )


@login_required
def control_acceso_guardia(request):
    empleado = _empleado_desde_user(request.user)

    ctx = {
        "empleado": empleado,
        "allowed_exit_states": ESTADOS_LIBERACION_OT,
        "vehiculo": None,
        "designacion": None,
        "control_abierto": None,
        "ot": None,                 # OT más reciente del vehículo
        "solicitud_ingreso": None,  # última solicitud para este vehículo

        "entrada_error": "",
        "entrada_ok": "",
        "salida_error": "",
        "salida_ok": "",

        "form_busqueda": {"patente": ""},
        "form_entrada": {
            "patente": "",
            "rut_chofer": "",
            "forzar": False,
            "motivo_forzado": "",
        },
        "form_salida": {
            "patente": "",
            "forzar": False,
            "motivo_forzado": "",
        },

        "mostrar_forzar_entrada": False,
        "mostrar_forzar_salida": False,
    }

    if not empleado:
        ctx["error_global"] = (
            "No se encontró el empleado asociado al usuario actual. "
            "Verifica que el campo 'usuario' de Empleado coincida con tu usuario Django."
        )
        return render(request, "control_acceso.html", ctx)

    # ======================================================
    # GET: solo búsqueda por patente (no registra nada)
    # ======================================================
    if request.method == "GET":
        patente_raw = _normalizar_patente(request.GET.get("patente"))
        ctx["form_busqueda"]["patente"] = patente_raw

        if patente_raw:
            vehiculo = Vehiculo.objects.filter(patente=patente_raw).first()
            if vehiculo:
                designacion = (
                    DesignacionVehicular.objects
                    .select_related("empleado")
                    .filter(
                        vehiculo=vehiculo,
                        fecha_fin__isnull=True,
                        estado="En uso",
                    )
                    .order_by("-fecha_inicio")
                    .first()
                )
                control_abierto = (
                    ControlAcceso.objects
                    .select_related("vehiculo", "chofer", "guardia_ingreso", "guardia_salida")
                    .filter(vehiculo=vehiculo, fecha_salida__isnull=True)
                    .order_by("-fecha_ingreso", "-control_id")
                    .first()
                )
                ot = (
                    OrdenTrabajo.objects
                    .filter(patente=vehiculo)
                    .order_by("-fecha_ingreso", "-hora_ingreso", "-ot_id")
                    .first()
                )
                # última solicitud de ingreso en el recinto del guardia
                solicitud_ingreso = (
                    SolicitudIngresoVehiculo.objects
                    .select_related("vehiculo", "chofer", "taller")
                    .filter(
                        vehiculo=vehiculo,
                        taller__recinto_id=empleado.recinto_id,
                        estado__in=["PENDIENTE", "APROBADA"],
                    )
                    .order_by("-fecha_solicitada", "-creado_en")
                    .first()
                )

                ctx["vehiculo"] = vehiculo
                ctx["designacion"] = designacion
                ctx["control_abierto"] = control_abierto
                ctx["ot"] = ot
                ctx["solicitud_ingreso"] = solicitud_ingreso

        return render(request, "control_acceso.html", ctx)

    # ======================================================
    # POST: entrada / salida
    # ======================================================
    accion = request.POST.get("accion")
    hoy = timezone.now().date()

    patente_raw = _normalizar_patente(request.POST.get("patente"))
    forzar = request.POST.get("forzar") == "on"
    motivo_forzado = (request.POST.get("motivo_forzado") or "").strip()

    ctx["form_busqueda"]["patente"] = patente_raw

    vehiculo = None
    designacion = None
    control_abierto = None
    ot = None
    solicitud_ingreso = None

    if patente_raw:
        vehiculo = Vehiculo.objects.filter(patente=patente_raw).first()

        if vehiculo:
            designacion = (
                DesignacionVehicular.objects
                .select_related("empleado")
                .filter(
                    vehiculo=vehiculo,
                    fecha_fin__isnull=True,
                    estado="En uso",
                )
                .order_by("-fecha_inicio")
                .first()
            )
            control_abierto = (
                ControlAcceso.objects
                .select_related("vehiculo", "chofer", "guardia_ingreso", "guardia_salida")
                .filter(vehiculo=vehiculo, fecha_salida__isnull=True)
                .order_by("-fecha_ingreso", "-control_id")
                .first()
            )
            ot = (
                OrdenTrabajo.objects
                .filter(patente=vehiculo)
                .order_by("-fecha_ingreso", "-hora_ingreso", "-ot_id")
                .first()
            )
            solicitud_ingreso = (
                SolicitudIngresoVehiculo.objects
                .select_related("vehiculo", "chofer", "taller")
                .filter(
                    vehiculo=vehiculo,
                    taller__recinto_id=empleado.recinto_id,
                    estado__in=["PENDIENTE", "APROBADA"],
                )
                .order_by("-fecha_solicitada", "-creado_en")
                .first()
            )

    ctx["vehiculo"] = vehiculo
    ctx["designacion"] = designacion
    ctx["control_abierto"] = control_abierto
    ctx["ot"] = ot
    ctx["solicitud_ingreso"] = solicitud_ingreso

    # =========================
    # ENTRADA AL RECINTO
    # =========================
    if accion == "entrada":
        rut_chofer_raw = (request.POST.get("rut_chofer") or "").strip()
        ctx["form_entrada"] = {
            "patente": patente_raw,
            "rut_chofer": rut_chofer_raw,
            "forzar": forzar,
            "motivo_forzado": motivo_forzado,
        }

        if not patente_raw:
            ctx["entrada_error"] = "Debe ingresar una patente para registrar la entrada."
            return render(request, "control_acceso.html", ctx)

        if not vehiculo:
            ctx["entrada_error"] = f"No existe el vehículo con patente {patente_raw}."
            return render(request, "control_acceso.html", ctx)

        # Si no se ingresa rut_chofer:
        # 1) usamos el chofer de la solicitud de ingreso (si existe)
        # 2) si no, el de la designación activa
        if not rut_chofer_raw:
            if solicitud_ingreso and solicitud_ingreso.chofer:
                rut_chofer_raw = solicitud_ingreso.chofer.rut
            elif designacion:
                rut_chofer_raw = designacion.empleado.rut

        if not rut_chofer_raw:
            ctx["entrada_error"] = (
                "Debe indicar el RUT del chofer o existir una solicitud de ingreso "
                "o una designación activa."
            )
            return render(request, "control_acceso.html", ctx)

        chofer = Empleado.objects.filter(rut=rut_chofer_raw).first()
        if not chofer:
            ctx["entrada_error"] = (
                f"No se encontró el chofer con RUT {rut_chofer_raw}."
            )
            return render(request, "control_acceso.html", ctx)

        if control_abierto:
            ctx["entrada_error"] = (
                f"Ya existe un ingreso abierto para la patente {vehiculo.patente} "
                f"({control_abierto.fecha_ingreso})."
            )
            return render(request, "control_acceso.html", ctx)

        # =========================
        # Validar chofer vs SolicitudIngreso y Designación
        # =========================
        expected_ruts = []
        if solicitud_ingreso and solicitud_ingreso.chofer:
            expected_ruts.append(
                f"{solicitud_ingreso.chofer.rut} — {solicitud_ingreso.chofer.nombre}"
            )
        if designacion:
            expected_ruts.append(
                f"{designacion.empleado.rut} — {designacion.empleado.nombre}"
            )

        rut_ok = True
        if expected_ruts:
            rut_ok = (
                (solicitud_ingreso and solicitud_ingreso.chofer
                 and solicitud_ingreso.chofer.rut == chofer.rut)
                or (designacion and designacion.empleado.rut == chofer.rut)
            )

        hay_mismatch = expected_ruts and not rut_ok
        ctx["mostrar_forzar_entrada"] = hay_mismatch

        if hay_mismatch and not forzar:
            lista_esperados = " / ".join(expected_ruts)
            ctx["entrada_error"] = (
                "El chofer ingresado no coincide con el chofer esperado. "
                "Debe registrar al chofer que hizo la solicitud de ingreso "
                "y/o al chofer designado para el vehículo. "
                f"Chofer(es) esperado(s): {lista_esperados}. "
                "Si corresponde continuar de todas maneras, marque 'Forzar operación' "
                "e indique el motivo."
            )
            return render(request, "control_acceso.html", ctx)

        if hay_mismatch and forzar and not motivo_forzado:
            ctx["entrada_error"] = (
                "Debe indicar un motivo de forzado cuando el chofer no coincide con "
                "la solicitud de ingreso o la designación vigente."
            )
            return render(request, "control_acceso.html", ctx)

        # Creamos el control de acceso (ingreso)
        ControlAcceso.objects.create(
            fecha_ingreso=hoy,
            fecha_salida=None,
            guardia_ingreso=empleado,
            vehiculo=vehiculo,
            guardia_salida=None,
            chofer=chofer,
            forzado=forzar or hay_mismatch,
            motivo_forzado=motivo_forzado if (forzar or hay_mismatch) else None,
        )

        # Marcamos el vehículo como "dentro del recinto" (NO en taller todavía)
        vehiculo.estado = ESTADO_VEHICULO_DENTRO  # -> "En Recinto"
        if empleado and empleado.recinto and hasattr(empleado.recinto, "ubicacion"):
            vehiculo.ubicacion = empleado.recinto.ubicacion
        vehiculo.save(update_fields=["estado", "ubicacion"])

        ctx["entrada_ok"] = (
            f"Ingreso registrado correctamente para {vehiculo.patente}. "
            f"Chofer: {chofer.rut} - {chofer.nombre}"
        )

        # Limpiamos formulario de entrada
        ctx["form_entrada"] = {
            "patente": "",
            "rut_chofer": "",
            "forzar": False,
            "motivo_forzado": "",
        }

        # Recalcular control_abierto
        ctx["control_abierto"] = (
            ControlAcceso.objects
            .filter(vehiculo=vehiculo, fecha_salida__isnull=True)
            .order_by("-fecha_ingreso", "-control_id")
            .first()
        )

        return render(request, "control_acceso.html", ctx)

    # =========================
    # SALIDA DEL RECINTO
    # =========================
    if accion == "salida":
        ctx["form_salida"] = {
            "patente": patente_raw,
            "forzar": forzar,
            "motivo_forzado": motivo_forzado,
        }

        if not patente_raw:
            ctx["salida_error"] = "Debe ingresar una patente para registrar la salida."
            return render(request, "control_acceso.html", ctx)

        if not vehiculo:
            ctx["salida_error"] = f"No existe el vehículo con patente {patente_raw}."
            return render(request, "control_acceso.html", ctx)

        if not control_abierto:
            ctx["salida_error"] = (
                f"No hay un ingreso abierto para la patente {vehiculo.patente}."
            )
            return render(request, "control_acceso.html", ctx)

        # Última OT del vehículo
        ot_estado_ok = ot and ot.estado in ESTADOS_LIBERACION_OT

        if not ot:
            mensaje_base = (
                "No se encontró una Orden de Trabajo para este vehículo. "
            )
        else:
            mensaje_base = (
                f"La última OT del vehículo (#{ot.ot_id}) está en estado '{ot.estado}'. "
            )

        # Mostrar bloque de forzado solo si la OT NO está en estado de liberación
        ctx["mostrar_forzar_salida"] = not ot_estado_ok

        if not ot_estado_ok and not forzar:
            ctx["salida_error"] = (
                mensaje_base
                + "Solo se permite la salida automática si la OT está en alguno de "
                f"los estados: {', '.join(ESTADOS_LIBERACION_OT)}. "
                "Si la salida debe realizarse de todas formas, marque 'Forzar operación' "
                "e indique el motivo."
            )
            return render(request, "control_acceso.html", ctx)

        if not ot_estado_ok and forzar and not motivo_forzado:
            ctx["salida_error"] = (
                "Debe indicar un motivo de forzado cuando la OT no está en un "
                "estado de liberación."
            )
            return render(request, "control_acceso.html", ctx)

        # Cerramos el control de acceso
        control_abierto.fecha_salida = hoy
        control_abierto.guardia_salida = empleado
        control_abierto.forzado = control_abierto.forzado or forzar

        if forzar and motivo_forzado:
            if control_abierto.motivo_forzado:
                control_abierto.motivo_forzado = (
                    control_abierto.motivo_forzado.strip()
                    + " | SALIDA: "
                    + motivo_forzado
                )
            else:
                control_abierto.motivo_forzado = motivo_forzado

        control_abierto.save()

        # Marcamos el vehículo como "fuera del recinto"
        vehiculo.estado = ESTADO_VEHICULO_FUERA  # -> "Disponible"
        vehiculo.save(update_fields=["estado"])

        ctx["salida_ok"] = (
            f"Salida registrada correctamente para {vehiculo.patente}. "
            f"Control #{control_abierto.control_id} cerrado."
        )

        ctx["form_salida"] = {
            "patente": "",
            "forzar": False,
            "motivo_forzado": "",
        }

        ctx["control_abierto"] = None
        return render(request, "control_acceso.html", ctx)

    # Si llega aquí con POST pero sin acción válida:
    return render(request, "control_acceso.html", ctx)
