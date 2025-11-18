from django.db import models

# MVP Nivel 2 → sin persistencia todavía
# Más adelante agregamos historial por empleado.
class ChatLog(models.Model):
    usuario = models.CharField(max_length=50)
    mensaje = models.TextField()
    sala = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.sala}] {self.usuario}: {self.mensaje[:20]}"
