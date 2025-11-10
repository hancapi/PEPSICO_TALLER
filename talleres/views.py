# talleres/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required(login_url="/inicio-sesion/")
def registro_taller(request):
    """
    Página de registro/operación de OTs en el taller.
    El listado y acciones se realizan vía JS contra los endpoints ya existentes:
      - GET  /api/ordenestrabajo/api/ingresos/en-curso/?taller_id=&fecha=
      - POST /api/ordenestrabajo/api/ingresos/<ot_id>/finalizar/
      - POST /api/ordenestrabajo/api/ingresos/<ot_id>/cancelar/
    """
    return render(request, "registro-taller.html")
