# documentos/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from ordenestrabajo.models import OrdenTrabajo
from vehiculos.models import Vehiculo
from .models import Documento

ALLOWED_EXT = {"jpg", "jpeg", "png", "pdf"}
MAX_SIZE_MB = 15

def _ext_ok(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def _size_ok(fobj) -> bool:
    return fobj.size <= MAX_SIZE_MB * 1024 * 1024

@require_http_methods(["GET"])
def document_list(request):
    """
    GET /api/documentos/?ot_id=123  |  /api/documentos/?patente=ABCZ12
    """
    ot_id = request.GET.get("ot_id")
    patente = request.GET.get("patente")

    if not ot_id and not patente:
        return JsonResponse({"success": False, "message": "Debe indicar ot_id o patente"}, status=400)

    qs = Documento.objects.all().order_by("-creado_en")
    if ot_id:
        qs = qs.filter(ot_id=ot_id)
    if patente:
        qs = qs.filter(patente_id=patente)

    data = [{
        "id": d.id,
        "titulo": d.titulo,
        "tipo": d.tipo,
        "ot_id": d.ot_id,
        "patente": d.patente_id,
        "archivo": d.archivo.url if d.archivo else None,
        "creado_en": d.creado_en.isoformat(),
    } for d in qs]
    return JsonResponse({"success": True, "documentos": data})

@csrf_exempt
@require_http_methods(["POST"])
def document_upload(request):
    """
    POST /api/documentos/upload/
    form-data:
      - archivo: file (jpg|jpeg|png|pdf; <= 15 MB)
      - titulo: str
      - tipo: FOTO|INFORME|OTRO (opcional)
      - ot_id: int (opcional)
      - patente: str (opcional)
    """
    f = request.FILES.get("archivo")
    titulo = (request.POST.get("titulo") or "").strip()
    tipo = (request.POST.get("tipo") or "OTRO").strip().upper()
    ot_id = request.POST.get("ot_id")
    patente = request.POST.get("patente")

    if not f or not titulo:
        return JsonResponse({"success": False, "message": "archivo y titulo son obligatorios"}, status=400)
    if not _ext_ok(f.name):
        return JsonResponse({"success": False, "message": "Extensión no permitida (jpg, jpeg, png, pdf)"}, status=400)
    if not _size_ok(f):
        return JsonResponse({"success": False, "message": f"Tamaño máximo {MAX_SIZE_MB}MB"}, status=400)

    ot = None
    veh = None
    if ot_id:
        try:
            ot = OrdenTrabajo.objects.get(pk=int(ot_id))
        except (ValueError, OrdenTrabajo.DoesNotExist):
            return JsonResponse({"success": False, "message": "OT no encontrada"}, status=404)
    if patente:
        try:
            veh = Vehiculo.objects.get(pk=patente)
        except Vehiculo.DoesNotExist:
            return JsonResponse({"success": False, "message": "Vehículo no encontrado"}, status=404)
    if not ot and not veh:
        return JsonResponse({"success": False, "message": "Debe indicar ot_id o patente"}, status=400)

    # Guardado por storage (MEDIA_ROOT)
    d = Documento(ot=ot, patente=veh, titulo=titulo, tipo=tipo)
    d.save()  # necesitamos ID para path dinámico

    # Ajusta upload_to según destino (ya lo hace el model.save(), pero aquí guardamos manualmente por seguridad)
    subdir = f"ordenes/{d.ot_id}" if d.ot_id else f"vehiculos/{d.patente_id}"
    path = default_storage.save(f"{subdir}/{f.name}", ContentFile(f.read()))
    d.archivo.name = path
    d.save(update_fields=["archivo"])

    return JsonResponse({
        "success": True,
        "documento": {
            "id": d.id, "titulo": d.titulo, "tipo": d.tipo,
            "ot_id": d.ot_id, "patente": d.patente_id,
            "archivo": d.archivo.url if d.archivo else None,
            "creado_en": d.creado_en.isoformat()
        }
    }, status=201)
