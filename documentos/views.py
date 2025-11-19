# documentos/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from ordenestrabajo.models import OrdenTrabajo
from vehiculos.models import Vehiculo
from .models import Documento


# ================================================================
# 🔵 NUEVO ENDPOINT COMPLETO: documentos agrupados
# ================================================================
@login_required
@require_http_methods(["GET"])
def document_list(request):

    ot_id = request.GET.get("ot_id")
    patente = request.GET.get("patente")

    if not ot_id and not patente:
        return JsonResponse({"success": False, "message": "Debe indicar ot_id o patente"}, status=400)

    # ----------------------------------------------------------------------------
    # A) DOCUMENTOS DE LA OT ACTUAL
    # ----------------------------------------------------------------------------
    docs_actual = []
    if ot_id:
        qs_actual = Documento.objects.filter(ot_id=ot_id).order_by("-creado_en")
        docs_actual = [
            {
                "id": d.id,
                "titulo": d.titulo,
                "tipo": d.tipo,
                "archivo": d.archivo.url if d.archivo else "",
                "creado_en": d.creado_en.strftime("%Y-%m-%d %H:%M"),
            }
            for d in qs_actual
        ]

    # ----------------------------------------------------------------------------
    # B) DOCUMENTOS DE OTs FINALIZADAS (distintas de la OT actual)
    # ----------------------------------------------------------------------------
    docs_finalizadas = []
    if patente:
        # OTs finalizadas del vehículo
        finalizadas = (
            OrdenTrabajo.objects
            .filter(patente_id=patente, estado="Finalizado")
            .exclude(ot_id=ot_id)
            .order_by("-ot_id")
        )

        for ot in finalizadas:
            qs_docs = Documento.objects.filter(ot_id=ot.ot_id).order_by("-creado_en")
            items = [
                {
                    "id": d.id,
                    "titulo": d.titulo,
                    "tipo": d.tipo,
                    "archivo": d.archivo.url if d.archivo else "",
                    "creado_en": d.creado_en.strftime("%Y-%m-%d %H:%M"),
                }
                for d in qs_docs
            ]

            if items:
                docs_finalizadas.append({
                    "ot_id": ot.ot_id,
                    "fecha": ot.fecha_ingreso.strftime("%Y-%m-%d"),
                    "docs": items
                })

    # ----------------------------------------------------------------------------
    # C) DOCUMENTOS DEL VEHÍCULO (sin OT)
    # ----------------------------------------------------------------------------
    docs_vehiculo = []
    if patente:
        qs_veh = Documento.objects.filter(ot_id__isnull=True, patente_id=patente).order_by("-creado_en")
        docs_vehiculo = [
            {
                "id": d.id,
                "titulo": d.titulo,
                "tipo": d.tipo,
                "archivo": d.archivo.url if d.archivo else "",
                "creado_en": d.creado_en.strftime("%Y-%m-%d %H:%M"),
            }
            for d in qs_veh
        ]

    return JsonResponse({
        "success": True,
        "actual": docs_actual,
        "finalizadas": docs_finalizadas,
        "vehiculo": docs_vehiculo,
    })
