from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required(login_url="/inicio-sesion/")
def chat_page(request):
    """
    Chat simple en tiempo real (MVP)
    """
    return render(request, "chat.html", {
        "usuario": request.user.username
    })
