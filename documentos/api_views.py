from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from .models import Documento
from ordenestrabajo.models import OrdenTrabajo


# ==========================================================
# GET — AGRUPAR DOCUMENTOS (OT actual, finalizadas, vehículo)
# ==========================================================
@login_required
@require_GET
def api_documentos_list(request):

    # Normalizar ot_id (puede venir "", "null", etc.)
    ot_id_raw = request.GET.get("ot_id")
    try:
        ot_id_actual = int(ot_id_raw) if ot_id_raw not in (None, "", "null") else None
    except (TypeError, ValueError):
        ot_id_actual = None

    patente = request.GET.get("patente")

    if not patente:
        return JsonResponse(
            {"success": False, "message": "Parámetro patente requerido"},
            status=400
        )

    # -------------------------------------------
    # 1) DOCUMENTOS OT ACTUAL
    # -------------------------------------------
    docs_actual = []
    if ot_id_actual is not None:
        qs_actual = Documento.objects.filter(ot_id=ot_id_actual).order_by("-creado_en")
        docs_actual = [
            {
                "id": d.id,
                "titulo": d.titulo,
                "tipo": d.tipo,
                "archivo": d.archivo.url if d.archivo else "",
                "creado_en": d.creado_en.strftime("%Y-%m-%d %H:%M"),
                "ot_id": d.ot_id,
            }
            for d in qs_actual
        ]

    # -------------------------------------------
    # 2) DOCUMENTOS OTs FINALIZADAS (agrupados)
    # -------------------------------------------
    ots_finalizadas_qs = OrdenTrabajo.objects.filter(
        patente_id=patente,
        estado="Finalizado"
    ).order_by("-fecha_ingreso", "-ot_id")

    # Si hay OT actual, la excluimos
    if ot_id_actual is not None:
        ots_finalizadas_qs = ots_finalizadas_qs.exclude(ot_id=ot_id_actual)

    grupos_finalizadas = []

    for ot in ots_finalizadas_qs:
        docs_ot = Documento.objects.filter(ot_id=ot.ot_id).order_by("-creado_en")

        if docs_ot.exists():
            grupos_finalizadas.append({
                "ot_id": ot.ot_id,
                "fecha": ot.fecha_ingreso.strftime("%Y-%m-%d"),
                "docs": [
                    {
                        "id": d.id,
                        "titulo": d.titulo,
                        "tipo": d.tipo,
                        "archivo": d.archivo.url if d.archivo else "",
                        "creado_en": d.creado_en.strftime("%Y-%m-%d %H:%M"),
                    }
                    for d in docs_ot
                ]
            })

    # -------------------------------------------
    # 3) DOCUMENTOS DEL VEHÍCULO (sin OT)
    # -------------------------------------------
    docs_vehiculo = Documento.objects.filter(
        patente_id=patente,
        ot_id__isnull=True
    ).order_by("-creado_en")

    lista_docs_vehiculo = [
        {
            "id": d.id,
            "titulo": d.titulo,
            "tipo": d.tipo,
            "archivo": d.archivo.url if d.archivo else "",
            "creado_en": d.creado_en.strftime("%Y-%m-%d %H:%M"),
        }
        for d in docs_vehiculo
    ]

    # -------------------------------------------
    # RESPUESTA FINAL (formato que consume ficha_vehiculo.js)
    # -------------------------------------------
    return JsonResponse({
        "success": True,
        "actual": docs_actual,
        "finalizadas": grupos_finalizadas,
        "vehiculo": lista_docs_vehiculo,
    })


# ==========================================================
# POST — SUBIR DOCUMENTO
# ==========================================================
@login_required
@require_POST
def api_documentos_upload(request):

    archivo = request.FILES.get("archivo")
    titulo = request.POST.get("titulo")
    tipo = request.POST.get("tipo") or "OTRO"

    # Normalizar ot_id igual que arriba
    ot_id_raw = request.POST.get("ot_id")
    try:
        ot_id = int(ot_id_raw) if ot_id_raw not in (None, "", "null") else None
    except (TypeError, ValueError):
        ot_id = None

    patente = request.POST.get("patente")

    if not archivo:
        return JsonResponse(
            {"success": False, "message": "Debe seleccionar un archivo."}
        )

    if not titulo:
        return JsonResponse(
            {"success": False, "message": "Debe ingresar un título."}
        )

    doc = Documento.objects.create(
        archivo=archivo,
        titulo=titulo,
        tipo=tipo,
        ot_id=ot_id,
        patente_id=patente or None,
    )

    return JsonResponse({
        "success": True,
        "documento": {
            "id": doc.id,
            "titulo": doc.titulo,
            "tipo": doc.tipo,
            "archivo": doc.archivo.url if doc.archivo else "",
            "creado_en": doc.creado_en.strftime("%Y-%m-%d %H:%M"),
            "ot_id": doc.ot_id,
            "patente": doc.patente_id,
        }
    })
