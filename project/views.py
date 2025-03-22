from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Aluno, Professor, Coordenador


def login(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        # Check if the user is an Aluno
        user = Aluno.objects.filter(emailAluno=email, senhaAluno=password).first()
        if not user:
            # Check if the user is a Professor
            user = Professor.objects.filter(emailProf=email, senhaProf=password).first()
        if not user:
            # Check if the user is a Coordenador
            user = Coordenador.objects.filter(
                emailCoord=email, senhaCoord=password
            ).first()

        if user:
            # Redirect to home page if credentials are correct
            return redirect("home")
        else:
            # Add an error message if credentials are incorrect
            messages.error(request, "Email ou senha incorretos.")

    return render(request, "index.html")


def resetPassword(request):
    return render(request, "forgot_password.html")

def home(request):
    return render(request, "home.html")

def atividades(request):
    return render(request, 'atividades.html')

def notas(request):
    return render(request, 'notas.html')

def disciplinas(request):
    return render(request, 'disciplinas.html')

def perfil(request):
    return render(request, 'perfil.html')
