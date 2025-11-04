#talleres/views.py
from rest_framework import viewsets
from .models import Taller
from .serializers import TallerSerializer
from django.shortcuts import render, get_object_or_404

# --- API REST ---
class TallerViewSet(viewsets.ModelViewSet):
    queryset = Taller.objects.all()
    serializer_class = TallerSerializer

# --- VISTA HTML ---
def registro_taller_view(request):
    talleres = Taller.objects.all()
    return render(request, 'talleres/registro_taller.html', {'talleres': talleres})
