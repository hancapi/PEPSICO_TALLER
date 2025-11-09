# --- API Pausas (añadir al final de ordenestrabajo/views.py) ---
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import OrdenTrabajo, Pausa

def _get_ot_or_404(ot_id):
    try:
        return OrdenTrabajo.objects.get(pk=ot_id)
    except OrdenTrabajo.DoesNotExist:
        return None

@csrf_exempt
@require_http_methods(["POST"])
def pausa_start(request, ot_id):
    ot = _get_ot_or_404(ot_id)
    if ot is None:
        return JsonResponse({"success": False, "message": "OT no encontrada"}, status=404)
    if Pausa.objects.filter(ot_id=ot_id, activo=True).exists():
        return JsonResponse({"success": False, "message": "Ya existe una pausa activa"}, status=400)

    motivo = (request.POST.get("motivo") or "Pausa iniciada").strip()
    p = Pausa.objects.create(ot_id=ot_id, motivo=motivo, inicio=timezone.now(), activo=True)
    return JsonResponse({
        "success": True,
        "pausa": {"id": p.id, "inicio": p.inicio.isoformat(), "motivo": p.motivo, "activo": p.activo}
    }, status=201)

@csrf_exempt
@require_http_methods(["POST"])
def pausa_stop(request, ot_id):
    ot = _get_ot_or_404(ot_id)
    if ot is None:
        return JsonResponse({"success": False, "message": "OT no encontrada"}, status=404)
    try:
        p = Pausa.objects.get(ot_id=ot_id, activo=True)
    except Pausa.DoesNotExist:
        return JsonResponse({"success": False, "message": "No hay pausa activa"}, status=400)

    p.fin = timezone.now()
    p.activo = False
    p.save(update_fields=["fin", "activo"])
    return JsonResponse({
        "success": True,
        "pausa": {"id": p.id, "fin": p.fin.isoformat(), "activo": p.activo}
    })

@require_http_methods(["GET"])
def pausa_list(request, ot_id):
    if _get_ot_or_404(ot_id) is None:
        return JsonResponse({"success": False, "message": "OT no encontrada"}, status=404)
    data = list(Pausa.objects.filter(ot_id=ot_id).order_by("-inicio").values(
        "id", "motivo", "inicio", "fin", "activo"
    ))
    return JsonResponse({"success": True, "pausas": data})
